import asyncio
import logging
import os
import secrets
import time
from typing import Literal

import httpx
from jinja2 import Template

from concerto import db

_DO_API_BASE = "https://api.digitalocean.com/v2"
_DEFAULT_IMAGE = "ubuntu-22-04-x64"
_KEYS_DIR = os.getenv("CONCERTO_KEYS_DIR", "/var/lib/concerto/keys")
_CLOUD_INIT_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "..", "..", "installer", "cloud_init.yaml.j2"
)
_CONCERTO_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")

# Region fallback order: if chosen region is unavailable (422), try these.
_REGION_FALLBACK: dict[str, list[str]] = {
    "nyc1": ["nyc3", "sfo3"],
    "nyc3": ["nyc1", "sfo3"],
    "sfo3": ["nyc3", "nyc1"],
    "fra1": ["ams3", "lon1"],
    "ams3": ["fra1", "lon1"],
    "lon1": ["fra1", "ams3"],
    "sgp1": ["blr1", "syd1"],
    "blr1": ["sgp1", "syd1"],
    "syd1": ["sgp1", "blr1"],
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
        "-C", f"concerto-{token[:8]}",
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
) -> str:
    """Create a droplet, handling 401/402/422 errors and auto-fallback on 422."""
    regions_to_try = [region] + _REGION_FALLBACK.get(region, [])
    last_error: Exception | None = None

    for r in regions_to_try:
        resp = await client.post(
            "/droplets",
            json={
                "name": name,
                "region": r,
                "size": size,
                "image": _DEFAULT_IMAGE,
                "user_data": cloud_init,
                "tags": [tag],
            },
        )
        if resp.status_code == 401:
            raise DOAuthError("DigitalOcean API returned 401 — check your API token")
        if resp.status_code == 402:
            raise DOCreditError("DigitalOcean account has insufficient credit")
        if resp.status_code == 422:
            last_error = Exception(f"Region/size unavailable: {r}/{size}")
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


async def destroy_droplet(do_api_key: str, droplet_id: str) -> None:
    """Destroy a droplet. Silently ignores errors (404 = already gone)."""
    headers = {"Authorization": f"Bearer {do_api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(base_url=_DO_API_BASE, headers=headers, timeout=15) as client:
            await client.delete(f"/droplets/{droplet_id}")
    except Exception:
        pass


async def provision_droplet(
    do_api_key: str,
    region: str,
    size: str,
    token: str,
    customer_email: str = "",
    mode: Literal["byoc", "hosted"] = "byoc",
) -> tuple[str, str, str, str]:
    """Returns (droplet_id, ipv4, ssh_private_key_path, ttyd_password).

    mode='hosted': Ethan's DO account, s-2vcpu-4gb, tagged concerto-hosted-<prefix>,
                   registered in concerto_hosted_pool.
    mode='byoc':   customer's DO key, customer-chosen size, tagged concerto.

    Raises:
        DOAuthError: DO API token is invalid (401).
        DOCreditError: DO account has insufficient credit (402).
        DropletBootError: Droplet entered error state during boot.
        TimeoutError: Droplet did not become active within 5 minutes.
    """
    private_key_path, public_key = await _generate_ssh_keypair(token)
    ttyd_password = secrets.token_hex(16)

    cloud_init = Template(_load_cloud_init_template()).render(
        token=token,
        ssh_public_key=public_key,
        ssh_authorized_key=public_key,
        concerto_api_base=_CONCERTO_API_BASE,
        concerto_token=token,
        concerto_callback_url=f"{_CONCERTO_API_BASE}/api/internal/droplet-ready",
        customer_email=customer_email,
        ttyd_password=ttyd_password,
    )

    tag = f"concerto-hosted-{token[:8]}" if mode == "hosted" else "concerto"
    headers = {"Authorization": f"Bearer {do_api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(
        base_url=_DO_API_BASE, headers=headers, timeout=30
    ) as client:
        droplet_id = await _create_droplet_with_fallback(
            client, f"concerto-{token[:8]}", region, size, cloud_init, tag
        )

        # Register hosted droplets immediately in the pool
        if mode == "hosted":
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
                        if mode == "hosted":
                            await db.upsert_hosted_pool(
                                droplet_id=droplet_id,
                                buyer_token=token,
                                ipv4=ipv4,
                                status="active",
                                created_at=int(time.time()),
                            )
                        return droplet_id, ipv4, private_key_path, ttyd_password

    raise TimeoutError(f"Droplet {droplet_id} did not become active within 5 minutes")
