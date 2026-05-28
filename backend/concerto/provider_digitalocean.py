"""
provider_digitalocean.py — DigitalOcean adapter implementing ProviderBase.

DELEGATES to the existing provisioner.py — does NOT duplicate DO logic.
The module-level functions import and call provisioner.py directly so that
all DO business logic (region fallback, snapshot checks, cloud-init rendering,
SSH key registration, polling) lives in exactly one place.

When provider_factory selects "do" (the default), callers get the same
byte-for-byte DO behaviour they have today.

Mapping (for reference):
  provision_droplet → provisioner.provision_droplet (provisioner.py:212–401)
  destroy_droplet   → provisioner.destroy_droplet   (provisioner.py:199–209)
  suspend           → POST /droplets/{id}/actions {"type":"power_off"}
  resume            → POST /droplets/{id}/actions {"type":"power_on"}
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from .provider_base import (
    DOAuthError,
    DOCreditError,
    DropletBootError,
    ProviderBase,
)

logger = logging.getLogger(__name__)

# DO size slugs — must match provisioner.py:35–38 exactly.
PLAN_TO_SIZE: dict[str, str] = {
    "solo": "s-2vcpu-4gb",
    "pro":  "s-2vcpu-8gb",
}

__all__ = [
    "provision_droplet",
    "destroy_droplet",
    "suspend",
    "resume",
    "PLAN_TO_SIZE",
    "DOAuthError",
    "DOCreditError",
    "DropletBootError",
]

_DO_API_BASE = "https://api.digitalocean.com/v2"


class DigitalOceanProvider(ProviderBase):
    """
    Thin adapter documenting the DO↔abstract mapping.
    Not instantiated in production — module-level functions delegate directly
    to provisioner.py to avoid any extra call overhead.
    """

    async def provision_droplet(
        self,
        api_key: str,
        region: str,
        size: str,
        token: str,
        customer_email: str = "",
        mode: Literal["byoc", "hosted", "solo", "pro", "trial"] = "byoc",
    ) -> tuple[str, str, str, str]:
        # Production: handled by the module-level function below.
        from concerto import provisioner as _do
        return await _do.provision_droplet(
            do_api_key=api_key, region=region, size=size,
            token=token, customer_email=customer_email, mode=mode,
        )

    async def destroy_droplet(
        self,
        api_key: str,
        vps_id: str,
        cf_tunnel_id: str = "",
    ) -> None:
        from concerto import provisioner as _do
        await _do.destroy_droplet(
            do_api_key=api_key, droplet_id=vps_id, cf_tunnel_id=cf_tunnel_id,
        )

    async def suspend(self, api_key: str, vps_id: str) -> None:
        """DO power-off: POST /droplets/{id}/actions {"type":"power_off"}."""
        if not api_key or not vps_id:
            return
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(
                    f"{_DO_API_BASE}/droplets/{vps_id}/actions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"type": "power_off"},
                )
        except Exception as exc:
            logger.warning("DO suspend vps_id=%s failed: %s", vps_id, exc)

    async def resume(self, api_key: str, vps_id: str) -> None:
        """DO power-on: POST /droplets/{id}/actions {"type":"power_on"}."""
        if not api_key or not vps_id:
            return
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(
                    f"{_DO_API_BASE}/droplets/{vps_id}/actions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"type": "power_on"},
                )
        except Exception as exc:
            logger.warning("DO resume vps_id=%s failed: %s", vps_id, exc)


# ── Module-level functions — identical signatures to existing provisioner.py ───
#
# These are what provider_factory re-exports. They delegate directly to
# provisioner.py so there is no double-layer of abstraction for the DO path.
# DEFAULT BEHAVIOUR: byte-for-byte identical to calling provisioner.py directly.


async def provision_droplet(
    do_api_key: str,
    region: str,
    size: str,
    token: str,
    customer_email: str = "",
    mode: Literal["byoc", "hosted", "solo", "pro", "trial"] = "byoc",
) -> tuple[str, str, str, str]:
    """
    Delegate to provisioner.provision_droplet — zero behaviour change for DO.

    provisioner.py:212–401 handles: SSH keypair generation, CF tunnel creation,
    cloud-init rendering, snapshot check, DO droplet creation with region fallback,
    IP polling, and hosted-pool registration.
    """
    from concerto import provisioner as _do
    return await _do.provision_droplet(
        do_api_key=do_api_key,
        region=region,
        size=size,
        token=token,
        customer_email=customer_email,
        mode=mode,
    )


async def destroy_droplet(
    api_key: str,
    vps_id: str,
    cf_tunnel_id: str = "",
) -> None:
    """
    Delegate to provisioner.destroy_droplet — zero behaviour change for DO.

    provisioner.py:199–209: DELETE /droplets/{droplet_id} + destroy_named_tunnel.
    Param names normalised: api_key→do_api_key, vps_id→droplet_id.
    """
    from concerto import provisioner as _do
    await _do.destroy_droplet(
        do_api_key=api_key,
        droplet_id=vps_id,
        cf_tunnel_id=cf_tunnel_id,
    )


_DO_API_KEY = os.getenv("DO_PROVISIONER_API_KEY", os.getenv("CONCERTO_DO_API_TOKEN", ""))


async def suspend(api_key: str, vps_id: str) -> None:
    """
    DO power-off via factory — replaces stripe_webhook._poweroff_droplet
    and hosted_lifecycle._do_power_off_droplet when routed through factory.
    """
    await DigitalOceanProvider().suspend(api_key=api_key, vps_id=vps_id)


async def resume(api_key: str, vps_id: str) -> None:
    """
    DO power-on via factory — replaces stripe_webhook._poweron_droplet
    when routed through factory.
    """
    await DigitalOceanProvider().resume(api_key=api_key, vps_id=vps_id)
