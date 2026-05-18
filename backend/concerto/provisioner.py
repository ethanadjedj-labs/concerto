import asyncio
import logging
import os
import re
import secrets
import time
from typing import Literal

import httpx
from jinja2 import Template

from concerto import db
from concerto.cf_tunnel import create_named_tunnel, destroy_named_tunnel

_DO_API_BASE = "https://api.digitalocean.com/v2"
_DEFAULT_IMAGE = "ubuntu-22-04-x64"
_KEYS_DIR = os.getenv("CONCERTO_KEYS_DIR", "/var/lib/concerto/keys")
_CLOUD_INIT_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "..", "..", "installer", "cloud_init.yaml.j2"
)
_CONCERTO_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")

# Hosted plan → DigitalOcean droplet size mapping
PLAN_TO_SIZE: dict[str, str] = {
    "solo": "s-2vcpu-4gb",
    "pro":  "s-2vcpu-8gb",
}

# Region fallback order: if chosen region is unavailable (422), try these.
# Cross-continent backups ensure 422 only fires if NO DO region has capacity.
_REGION_FALLBACK: dict[str, list[str]] = {
    # US
    "nyc1": ["nyc3", "sfo3", "sfo2", "tor1", "ams3", "fra1"],
    "nyc3": ["nyc1", "sfo3", "sfo2", "tor1", "ams3", "fra1"],
    "sfo3": ["nyc3", "nyc1", "sfo2", "tor1", "ams3", "fra1"],
    "sfo2": ["sfo3", "nyc3", "nyc1", "tor1", "ams3", "fra1"],
    "tor1": ["nyc3", "nyc1", "sfo3", "ams3", "lon1", "fra1"],
    # EU
    "fra1": ["ams3", "lon1", "nyc1", "nyc3", "sfo3"],
    "ams3": ["fra1", "lon1", "nyc1", "nyc3", "sfo3"],
    "lon1": ["fra1", "ams3", "nyc1", "nyc3", "sfo3"],
    # APAC
    "sgp1": ["blr1", "syd1", "fra1", "ams3", "nyc1"],
    "blr1": ["sgp1", "syd1", "fra1", "ams3", "nyc1"],
    "syd1": ["sgp1", "blr1", "fra1", "ams3", "nyc1"],
}

_STUB_CLOUD_INIT = """\
#cloud-config
package_update: true

packages:
  - curl
  - wget
  - jq

runcmd:
  - mkdir -p /root/.ssh && chmod 700 /root/.ssh
  - echo "{{ ssh_public_key }}" >> /root/.ssh/authorized_keys
  - chmod 600 /root/.ssh/authorized_keys
  - |
    TTYD_VER=$(curl -sf https://api.github.com/repos/tsl0922/ttyd/releases/latest | jq -r '.tag_name' || echo "1.7.4")
    wget -qO /usr/local/bin/ttyd "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VER}/ttyd.x86_64"
    chmod +x /usr/local/bin/ttyd
  - nohup ttyd --port 7681 --interface 127.0.0.1 --credential concerto:{{ ttyd_password }} bash >/var/log/ttyd.log 2>&1 &
  - |
    sleep 15
    curl -sf -X POST {{ concerto_api_base }}/api/internal/droplet-ready \\
      -H 'Content-Type: application/json' \\
      -d '{"token":"{{ token }}","mcp_url":"stub://pending","bearer_token":"stub","ttyd_url":"stub://pending/terminal"}' || true
"""

logger = logging.getLogger(__name__)


class DOAuthError(Exception):
    """DO API returned 401 — invalid or expired API token."""


class DOCreditError(Exception):
    """DO API returned 402 — account has insufficient credit."""


class DropletBootError(Exception):
    """Droplet created but entered error status during boot."""


def _load_cloud_init_template() -> str:
    try:
        with open(_CLOUD_INIT_TEMPLATE) as f:
            return f.read()
    except FileNotFoundError:
        return _STUB_CLOUD_INIT


async def _generate_ssh_keypair(token: str) -> tuple[str, str]:
    os.makedirs(_KEYS_DIR, exist_ok=True)
    os.chmod(_KEYS_DIR, 0o700)
    key_path = os.path.join(_KEYS_DIR, f"{token}.pem")
    pub_path = f"{key_path}.pub"

    proc = await asyncio.create_subprocess_exec(
        "ssh-keygen", "-t", "ed25519", "-f", key_path, "-N", "",
        "-C", f"concerto-{token[:8].replace("_", "-")}",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    os.chmod(key_path, 0o600)

    with open(pub_path) as f:
        pub_key = f.read().strip()

    return key_path, pub_key


async def _create_droplet_with_fallback(
    client: httpx.AsyncClient,
    name: str,
    region: str,
    size: str,
    cloud_init: str,
    tag: str,
    ssh_key_ids: list[int] | None = None,
) -> str:
    """Create a droplet, handling 401/402/422 errors and auto-fallback on 422."""
    regions_to_try = [region] + _REGION_FALLBACK.get(region, [])
    last_error: Exception | None = None

    for r in regions_to_try:
        _body: dict = {
            "name": name,
            "region": r,
            "size": size,
            "image": _DEFAULT_IMAGE,
            "user_data": cloud_init,
            "tags": [tag],
        }
        if ssh_key_ids:
            _body["ssh_keys"] = ssh_key_ids
        resp = await client.post("/droplets", json=_body)
        if resp.status_code == 401:
            raise DOAuthError("DigitalOcean API returned 401 — check your API token")
        if resp.status_code == 402:
            raise DOCreditError("DigitalOcean account has insufficient credit")
        if resp.status_code == 422:
            try:
                err_body = resp.json()
            except Exception:
                err_body = {"raw": resp.text[:500]}
            logger.error("DO 422 for region=%s size=%s body=%s", r, size, err_body)
            last_error = Exception(f"Region/size unavailable: {r}/{size} - {err_body}")
            continue
        resp.raise_for_status()
        droplet_id = str(resp.json()["droplet"]["id"])
        if r != region:
            logger.warning(
                "Region %s unavailable; provisioned in fallback region %s (droplet %s)",
                region, r, droplet_id,
            )
        return droplet_id

    raise last_error or Exception("All regions unavailable for this size")


async def destroy_droplet(do_api_key: str, droplet_id: str, cf_tunnel_id: str = "") -> None:
    """Destroy a droplet and its associated CF tunnel. Silently ignores errors."""
    headers = {"Authorization": f"Bearer {do_api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(base_url=_DO_API_BASE, headers=headers, timeout=15) as client:
            await client.delete(f"/droplets/{droplet_id}")
    except Exception:
        pass

    if cf_tunnel_id:
        await destroy_named_tunnel(cf_tunnel_id)


async def provision_droplet(
    do_api_key: str,
    region: str,
    size: str,
    token: str,
    customer_email: str = "",
    mode: Literal["byoc", "hosted", "solo", "pro"] = "byoc",
) -> tuple[str, str, str, str]:
    """Returns (droplet_id, ipv4, ssh_private_key_path, ttyd_password).

    mode='solo': Ethan's DO account, s-2vcpu-4gb, tagged concerto-solo-<prefix>.
    mode='pro':  Ethan's DO account, s-2vcpu-8gb, tagged concerto-pro-<prefix>.
    mode='hosted': Legacy alias for 'solo' (grandfathered).
    mode='byoc':   customer's DO key, customer-chosen size, tagged concerto-byoc-<prefix>.

    Raises:
        DOAuthError: DO API token is invalid (401).
        DOCreditError: DO account has insufficient credit (402).
        DropletBootError: Droplet entered error state during boot.
        TimeoutError: Droplet did not become active within 5 minutes.
    """
    # Normalise legacy 'hosted' → 'solo'
    if mode == "hosted":
        mode = "solo"

    private_key_path, public_key = await _generate_ssh_keypair(token)
    ttyd_password = secrets.token_hex(16)

    # Create named CF tunnel before droplet so the stable hostname is ready.
    # Covers solo/pro/trial (all use the platform DO account); byoc gets ephemeral tunnel.
    is_hosted = mode in ("solo", "pro", "trial")
    tunnel_info: dict = {}
    if is_hosted:
        tunnel_info = await create_named_tunnel(token)
        await db.update_buyer(token, cf_tunnel_id=tunnel_info["tunnel_id"])

    # Sanitize email to safe chars before rendering into shell-sourced env file (Bug #24)
    safe_email = re.sub(r"[^a-zA-Z0-9.+\-_@]", "", customer_email or "")

    cloud_init = Template(_load_cloud_init_template()).render(
        token=token,
        ssh_public_key=public_key,
        ssh_authorized_key=public_key,
        concerto_api_base=_CONCERTO_API_BASE,
        concerto_token=token,
        concerto_token_prefix=token[:8].replace("_", "-"),
        concerto_callback_url=f"{_CONCERTO_API_BASE}/api/internal/droplet-ready",
        customer_email=safe_email,
        ttyd_password=ttyd_password,
        tunnel_token=tunnel_info.get("tunnel_token", ""),
        tunnel_hostname=tunnel_info.get("hostname", ""),
    )

    tag = f"concerto-{mode}-{token[:8].replace("_", "-")}" if is_hosted else f"concerto-byoc-{token[:8].replace("_", "-")}"

    # For platform-hosted plans use PLAN_TO_SIZE (trial keeps its caller-supplied size)
    if mode in ("solo", "pro"):
        size = PLAN_TO_SIZE.get(mode, "s-2vcpu-4gb")

    headers = {"Authorization": f"Bearer {do_api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(
            base_url=_DO_API_BASE, headers=headers, timeout=30
        ) as client:
            # Sanitize: DO requires [a-z0-9-], no consecutive/leading/trailing hyphens
            _raw = f"concerto-{token[:8].lower()}"
            _safe = re.sub(r"[^a-z0-9-]", "-", _raw)
            _safe = re.sub(r"-+", "-", _safe).strip("-")
            droplet_name = (_safe[:63] or "concerto-trial")
            # Register public key with DO account — DO injects it at image-level
            # BEFORE cloud-init runs (guaranteed SSH access from first boot)
            _do_key_id: int | None = None
            try:
                _kr = await client.post("/account/keys", json={
                    "name": f"concerto-tmp-{token[:8]}",
                    "public_key": public_key,
                })
                if _kr.status_code in (200, 201):
                    _do_key_id = _kr.json()["ssh_key"]["id"]
                    logger.info("Registered tmp DO SSH key id=%s for token %.8s", _do_key_id, token)
            except Exception as _ke:
                logger.warning("Could not register SSH key with DO: %s", _ke)

            droplet_id = await _create_droplet_with_fallback(
                client, droplet_name, region, size, cloud_init, tag,
                ssh_key_ids=[_do_key_id] if _do_key_id else None,
            )

            # Remove temp key from DO account immediately after droplet creation
            if _do_key_id:
                try:
                    await client.delete(f"/account/keys/{_do_key_id}")
                    logger.info("Deleted tmp DO SSH key id=%s", _do_key_id)
                except Exception as _de:
                    logger.warning("Could not delete tmp DO SSH key %s: %s", _do_key_id, _de)

            # Register solo/pro droplets in the hosted pool (trial has its own concerto_buyers row)
            if mode in ("solo", "pro"):
                await db.upsert_hosted_pool(
                    droplet_id=droplet_id,
                    buyer_token=token,
                    ipv4=None,
                    status="provisioning",
                    created_at=int(time.time()),
                )

            # Poll for active + public IP (max 5 min)
            for _ in range(60):
                await asyncio.sleep(5)
                r = await client.get(f"/droplets/{droplet_id}")
                r.raise_for_status()
                d = r.json()["droplet"]
                if d["status"] == "error":
                    raise DropletBootError(
                        f"Droplet {droplet_id} entered error state during boot"
                    )
                if d["status"] == "active":
                    for net in d.get("networks", {}).get("v4", []):
                        if net["type"] == "public":
                            ipv4 = net["ip_address"]
                            if mode in ("solo", "pro"):
                                await db.upsert_hosted_pool(
                                    droplet_id=droplet_id,
                                    buyer_token=token,
                                    ipv4=ipv4,
                                    status="active",
                                    created_at=int(time.time()),
                                )
                            return droplet_id, ipv4, private_key_path, ttyd_password

    except Exception:
        # CF tunnel was created but droplet creation/boot failed — clean it up
        if is_hosted and tunnel_info.get("tunnel_id"):
            try:
                await destroy_named_tunnel(tunnel_info["tunnel_id"])
            except Exception:
                pass
        raise

    raise TimeoutError(f"Droplet {droplet_id} did not become active within 5 minutes")
