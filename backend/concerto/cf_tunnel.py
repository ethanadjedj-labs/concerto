"""
Cloudflare named tunnel management for per-customer Concerto workspaces.

Each customer gets a named CF tunnel (concerto-{token_prefix}) with a stable
hostname {token_prefix}.workspaces.concerto.run that survives droplet reboots.
"""

from __future__ import annotations

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


async def create_named_tunnel(token: str) -> dict:
    """Create a named CF tunnel for this customer.

    Returns:
        {
          "tunnel_id": "uuid",
          "tunnel_token": "eyJ...",
          "hostname": "{token_prefix}.workspaces.concerto.run",
        }
    """
    token_prefix = token[:8].lower()
    hostname = f"{token_prefix}.workspaces.concerto.run"
    account_id = _cf_account_id()
    headers = _cf_headers()

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Create the named tunnel
        resp = await client.post(
            f"{_CF_API}/accounts/{account_id}/cfd_tunnel",
            headers=headers,
            json={"name": f"concerto-{token_prefix}", "config_src": "cloudflare"},
        )
        resp.raise_for_status()
        result = resp.json()["result"]
        tunnel_id: str = result["id"]
        tunnel_token: str = result["token"]

        logger.info("Created CF tunnel %s (%s) for prefix=%s", tunnel_id, hostname, token_prefix)

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

        # 3. Create DNS CNAME: {token_prefix}.workspaces → {tunnel_id}.cfargotunnel.com
        resp = await client.post(
            f"{_CF_API}/zones/{_ZONE_ID}/dns_records",
            headers=headers,
            json={
                "type": "CNAME",
                "name": f"{token_prefix}.workspaces",
                "content": f"{tunnel_id}.cfargotunnel.com",
                "proxied": True,
                "ttl": 1,
            },
        )
        resp.raise_for_status()
        logger.info("Created DNS CNAME %s → %s.cfargotunnel.com", hostname, tunnel_id)

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
        # Delete the tunnel (CF also cleans up associated DNS when tunnel deleted)
        try:
            resp = await client.delete(
                f"{_CF_API}/accounts/{account_id}/cfd_tunnel/{tunnel_id}",
                headers=headers,
            )
            if resp.status_code not in (200, 404):
                logger.warning("CF tunnel delete %s returned %s", tunnel_id, resp.status_code)
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
