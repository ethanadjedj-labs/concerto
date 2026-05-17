import asyncio
import os
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from maestro import db, provisioner

router = APIRouter()

_HOSTED_SIZE = "s-2vcpu-4gb"
_MAESTRO_DO_API_TOKEN = os.getenv("MAESTRO_DO_API_TOKEN", "")


class ProvisionRequest(BaseModel):
    token: str
    do_api_key: str = ""  # required for byoc, unused for hosted
    region: str = "nyc3"
    size: str = "s-1vcpu-1gb"  # byoc only; hosted always uses _HOSTED_SIZE


class DropletReadyPayload(BaseModel):
    token: str
    mcp_url: str
    bearer_token: str
    ttyd_url: str = ""  # F5: droplet POSTs the trycloudflare URL for ttyd


@router.post("/api/provision", status_code=202)
async def provision(req: ProvisionRequest):
    buyer = await db.get_buyer(req.token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Token not found")
    if buyer["status"] != "paid_unprovisioned":
        raise HTTPException(
            status_code=409,
            detail=f"Token is in unexpected state: {buyer['status']}",
        )

    plan = buyer.get("plan", "byoc")

    if plan == "hosted":
        if not _MAESTRO_DO_API_TOKEN:
            raise HTTPException(
                status_code=503,
                detail="Hosted provisioning unavailable: MAESTRO_DO_API_TOKEN not configured",
            )
        await db.update_buyer(
            req.token, status="provisioning", region=req.region, vps_size=_HOSTED_SIZE
        )
        asyncio.create_task(
            _provision_async(
                req.token,
                _MAESTRO_DO_API_TOKEN,
                req.region,
                _HOSTED_SIZE,
                mode="hosted",
            )
        )
    else:
        if not req.do_api_key:
            raise HTTPException(
                status_code=422,
                detail="do_api_key is required for BYOC plan",
            )
        await db.update_buyer(
            req.token, status="provisioning", region=req.region, vps_size=req.size
        )
        asyncio.create_task(
            _provision_async(
                req.token, req.do_api_key, req.region, req.size, mode="byoc"
            )
        )

    return {"status": "provisioning", "token": req.token, "plan": plan}


async def _provision_async(
    token: str, do_api_key: str, region: str, size: str, mode: str = "byoc"
) -> None:
    try:
        buyer = await db.get_buyer(token)
        customer_email = buyer["email"] if buyer else ""

        droplet_id, vps_ip, ssh_key_path, ttyd_password = await provisioner.provision_droplet(
            do_api_key=do_api_key,
            region=region,
            size=size,
            token=token,
            customer_email=customer_email,
            mode=mode,
        )
        await db.update_buyer(
            token,
            vps_id=droplet_id,
            vps_ip=vps_ip,
            ssh_keypair_private_path=ssh_key_path,
            ttyd_password=ttyd_password,
            status="installing",
            provisioned_at=int(time.time()),
        )
    except Exception as exc:
        err_msg = f"error:{type(exc).__name__}:{str(exc)[:100]}"
        await db.update_buyer(token, status=err_msg)


@router.post("/api/internal/droplet-ready")
async def droplet_ready(payload: DropletReadyPayload):
    """F5: droplet POSTs here once cloudflared tunnel URL is captured."""
    buyer = await db.get_buyer(payload.token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Token not found")

    await db.update_buyer(
        payload.token,
        mcp_url=payload.mcp_url,
        bearer_token=payload.bearer_token,
        ttyd_public_url=payload.ttyd_url,
        status="awaiting_oauth",
        installed_at=int(time.time()),
    )
    return {"ok": True}
