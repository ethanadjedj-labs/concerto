"""
Cloudflare named tunnel management for per-customer Concerto workspaces.

Each customer gets a named CF tunnel with a stable hostname derived from the
full token via SHA-256: c{sha256(token)[:16]}.workspaces.concerto.run

This replaces the old token[:8].lower() scheme which could produce collisions
(different tokens with the same first 8 chars after lowercasing).

Reliability guarantees:
  - Deterministic: same token → same label → same hostname, always.
  - Collision-free in practice: 64-bit hash space, negligible birthday probability.
  - DNS-valid: label is 'c' + 16 hex chars = 17 chars, only [a-z0-9], starts with letter.
  - Fail-loud: if a different tunnel already owns the hostname, provisioning aborts.
  - Idempotent: if the same tunnel already owns the hostname (re-provision), reuses it.
"""

from __future__ import annotations

import hashlib
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_CF_API = "https://api.cloudflare.com/client/v4"
_ZONE_ID = "208681448c90a193489a0907a48f6166"  # concerto.run zone


def _cf_headers() -> dict[str, str]:
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _cf_account_id() -> str:
    return os.environ["CLOUDFLARE_ACCOUNT_ID"]


def _derive_label(token: str) -> str:
    """Return the DNS label for this token: 'c' + sha256(token)[:16hex].

    Properties:
      - 17 chars, only [a-z0-9], starts with 'c' (DNS-valid).
      - Deterministic: same token → same label, always.
      - Collision-free in practice: 64-bit hash space.
      - Never truncates or lowercases the raw token — hashes the full value.
    """
    return "c" + hashlib.sha256(token.encode()).hexdigest()[:16]


async def create_named_tunnel(token: str) -> dict:
    """Create (or idempotently reuse) a named CF tunnel for this customer.

    Hostname format: c{sha256(token)[:16]}.workspaces.concerto.run

    Uniqueness guarantee: queries CF DNS for an existing CNAME before creating one.
      - No existing record → create it.
      - Existing record for THIS tunnel (idempotent re-provision) → reuse.
      - Existing record for a DIFFERENT tunnel (should-never-happen collision) →
        raises RuntimeError immediately; never silently overwrites.

    Returns:
        {
          "tunnel_id": "uuid",
          "tunnel_token": "eyJ...",
          "hostname": "c<16hex>.workspaces.concerto.run",
        }
    """
    label = _derive_label(token)
    hostname = f"{label}.workspaces.concerto.run"
    tunnel_name = f"concerto-{label}"
    account_id = _cf_account_id()
    headers = _cf_headers()

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Create the named tunnel (idempotent: if name already exists, look it up)
        resp = await client.post(
            f"{_CF_API}/accounts/{account_id}/cfd_tunnel",
            headers=headers,
            json={"name": tunnel_name, "config_src": "cloudflare"},
        )

        if resp.status_code in (200, 201):
            result = resp.json()["result"]
            tunnel_id: str = result["id"]
            tunnel_token: str = result["token"]
            logger.info("Created CF tunnel %s (%s) label=%s", tunnel_id, hostname, label)
        elif resp.status_code in (400, 409):
            # Tunnel name already exists (idempotent re-provision or partial cleanup).
            # Look it up by name and reuse the existing tunnel.
            logger.info(
                "CF tunnel name %r already exists (HTTP %s) — looking up existing tunnel",
                tunnel_name, resp.status_code,
            )
            list_resp = await client.get(
                f"{_CF_API}/accounts/{account_id}/cfd_tunnel",
                headers=headers,
                params={"name": tunnel_name, "is_deleted": "false"},
            )
            list_resp.raise_for_status()
            existing = list_resp.json().get("result", [])
            if not existing:
                raise RuntimeError(
                    f"CF tunnel name {tunnel_name!r} reported conflict (HTTP {resp.status_code}) "
                    f"but name lookup found nothing. Original error: {resp.text[:300]}"
                )
            tunnel_id = existing[0]["id"]
            # The list API does not return the tunnel token; fetch it via the dedicated endpoint.
            tok_resp = await client.get(
                f"{_CF_API}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token",
                headers=headers,
            )
            tok_resp.raise_for_status()
            tunnel_token = tok_resp.json()["result"]
            logger.info("Reusing existing CF tunnel %s (%s) label=%s", tunnel_id, hostname, label)
        else:
            resp.raise_for_status()
            raise RuntimeError(f"Unexpected CF response creating tunnel: HTTP {resp.status_code}")

        # 2. Configure ingress: hostname → localhost:8080
        resp = await client.put(
            f"{_CF_API}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",
            headers=headers,
            json={
                "config": {
                    "ingress": [
                        {"hostname": hostname, "service": "http://localhost:8080"},
                        {"service": "http_status:404"},
                    ],
                }
            },
        )
        resp.raise_for_status()

        # 3. Active uniqueness check: verify no conflicting CNAME before creating one.
        expected_content = f"{tunnel_id}.cfargotunnel.com"
        dns_check = await client.get(
            f"{_CF_API}/zones/{_ZONE_ID}/dns_records",
            headers=headers,
            params={"name": hostname, "type": "CNAME"},
        )
        dns_check.raise_for_status()
        existing_records = dns_check.json().get("result", [])

        if existing_records:
            existing_content = existing_records[0].get("content", "")
            if existing_content == expected_content:
                # Idempotent: same tunnel already owns this hostname — nothing to do.
                logger.info(
                    "DNS CNAME %s → %s already correct — reusing", hostname, tunnel_id
                )
            else:
                # COLLISION: a different tunnel owns this hostname.
                # With hash-based labels this should never happen, but if it does we
                # MUST NOT silently overwrite — raise immediately so it surfaces.
                logger.error(
                    "COLLISION DETECTED: DNS CNAME %s points to %s but we expected %s "
                    "(token %.8s, tunnel %s). Provisioning aborted.",
                    hostname, existing_content, expected_content, token, tunnel_id,
                )
                raise RuntimeError(
                    f"Hostname collision on {hostname}: already assigned to a different "
                    f"CF tunnel ({existing_content} != {expected_content}). "
                    "This must be investigated immediately — provisioning aborted."
                )
        else:
            # No existing record — create it.
            dns_resp = await client.post(
                f"{_CF_API}/zones/{_ZONE_ID}/dns_records",
                headers=headers,
                json={
                    "type": "CNAME",
                    "name": f"{label}.workspaces",
                    "content": expected_content,
                    "proxied": True,
                    "ttl": 1,
                },
            )
            dns_resp.raise_for_status()
            logger.info("Created DNS CNAME %s → %s", hostname, tunnel_id)

    return {
        "tunnel_id": tunnel_id,
        "tunnel_token": tunnel_token,
        "hostname": hostname,
    }


async def destroy_named_tunnel(tunnel_id: str) -> None:
    """Best-effort delete of a named CF tunnel and its DNS record."""
    if not tunnel_id:
        return
    cf_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not cf_token or not account_id:
        logger.warning("CF env vars missing — skipping tunnel cleanup for %s", tunnel_id)
        return

    headers = {"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        # Delete the tunnel with force=true (works even if cloudflared is still connected)
        try:
            resp = await client.delete(
                f"{_CF_API}/accounts/{account_id}/cfd_tunnel/{tunnel_id}",
                headers=headers,
                params={"force": "true"},
            )
            if resp.status_code not in (200, 404):
                logger.warning("CF tunnel delete %s returned %s: %s",
                               tunnel_id, resp.status_code, resp.text[:200])
            else:
                logger.info("Deleted CF tunnel %s", tunnel_id)
        except Exception as exc:
            logger.warning("CF tunnel delete %s failed: %s", tunnel_id, exc)

        # Also sweep any lingering DNS CNAME records pointing at this tunnel
        try:
            resp = await client.get(
                f"{_CF_API}/zones/{_ZONE_ID}/dns_records",
                headers=headers,
                params={"content": f"{tunnel_id}.cfargotunnel.com", "type": "CNAME"},
            )
            if resp.status_code == 200:
                for rec in resp.json().get("result", []):
                    rec_id = rec["id"]
                    await client.delete(
                        f"{_CF_API}/zones/{_ZONE_ID}/dns_records/{rec_id}",
                        headers=headers,
                    )
                    logger.info("Deleted DNS record %s for tunnel %s", rec_id, tunnel_id)
        except Exception as exc:
            logger.warning("CF DNS cleanup for tunnel %s failed: %s", tunnel_id, exc)
