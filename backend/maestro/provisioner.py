import asyncio
import os
import secrets
import time
from typing import Literal

import httpx
from jinja2 import Template

from maestro import db

_DO_API_BASE = "https://api.digitalocean.com/v2"
_DEFAULT_IMAGE = "ubuntu-22-04-x64"
_KEYS_DIR = os.getenv("MAESTRO_KEYS_DIR", "/var/lib/maestro/keys")
_CLOUD_INIT_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "..", "..", "installer", "cloud_init.yaml.j2"
)
_MAESTRO_API_BASE = os.getenv("MAESTRO_API_BASE", "https://api.maestro.run")

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
  - nohup ttyd --port 7681 --interface 127.0.0.1 --credential maestro:{{ ttyd_password }} bash >/var/log/ttyd.log 2>&1 &
  - |
    sleep 15
    curl -sf -X POST {{ maestro_api_base }}/api/internal/droplet-ready \\
      -H 'Content-Type: application/json' \\
      -d '{"token":"{{ token }}","mcp_url":"stub://pending","bearer_token":"stub","ttyd_url":"stub://pending/terminal"}' || true
"""


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
        "-C", f"maestro-{token[:8]}",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    os.chmod(key_path, 0o600)

    with open(pub_path) as f:
        pub_key = f.read().strip()

    return key_path, pub_key


async def provision_droplet(
    do_api_key: str,
    region: str,
    size: str,
    token: str,
    customer_email: str = "",
    mode: Literal["byoc", "hosted"] = "byoc",
) -> tuple[str, str, str, str]:
    """Returns (droplet_id, ipv4, ssh_private_key_path, ttyd_password).

    mode='hosted': Ethan's DO account, s-2vcpu-4gb, tagged maestro-hosted-<prefix>,
                   registered in maestro_hosted_pool.
    mode='byoc':   customer's DO key, customer-chosen size, tagged maestro.
    """
    private_key_path, public_key = await _generate_ssh_keypair(token)
    ttyd_password = secrets.token_hex(16)

    cloud_init = Template(_load_cloud_init_template()).render(
        token=token,
        ssh_public_key=public_key,
        ssh_authorized_key=public_key,
        maestro_api_base=_MAESTRO_API_BASE,
        maestro_token=token,
        maestro_callback_url=f"{_MAESTRO_API_BASE}/api/internal/droplet-ready",
        customer_email=customer_email,
        ttyd_password=ttyd_password,
    )

    tag = f"maestro-hosted-{token[:8]}" if mode == "hosted" else "maestro"

    headers = {
        "Authorization": f"Bearer {do_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(
        base_url=_DO_API_BASE, headers=headers, timeout=30
    ) as client:
        resp = await client.post(
            "/droplets",
            json={
                "name": f"maestro-{token[:8]}",
                "region": region,
                "size": size,
                "image": _DEFAULT_IMAGE,
                "user_data": cloud_init,
                "tags": [tag],
            },
        )
        resp.raise_for_status()
        droplet_id = str(resp.json()["droplet"]["id"])

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
