import asyncio
import logging
import os
import time

import hmac

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from concerto import db, provider_factory as provisioner
from concerto.email_utils import send_operator_alert

router = APIRouter()
logger = logging.getLogger(__name__)

_CLOUD_INIT_TIMEOUT_S = 8 * 60  # 8 minutes
_MANAGER_STATE_PATH = "/opt/cortex/OPS/MANAGER_STATE.md"
_HOSTED_SIZE = "s-2vcpu-4gb"
_CONCERTO_DO_API_TOKEN = os.getenv("CONCERTO_DO_API_TOKEN", "")
_FRONTEND_URL = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")


class ProvisionRequest(BaseModel):
    token: str
    do_api_key: str = ""  # required for byoc, unused for hosted
    region: str = "nyc3"
    size: str = "s-1vcpu-1gb"  # byoc only; hosted always uses _HOSTED_SIZE


class DropletReadyPayload(BaseModel):
    token: str
    mcp_url: str
    bearer_token: str
    ttyd_url: str = ""


@router.post("/api/provision", status_code=202)
async def provision(req: ProvisionRequest):
    buyer = await db.get_buyer(req.token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Token not found")

    if buyer["status"] not in (
        "paid_unprovisioned",
        "api_key_invalid",
        "account_no_credit",
        "provisioning_failed",
        "provisioning_timeout",
        "failed_install",
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Token is in unexpected state: {buyer['status']}",
        )

    plan = buyer.get("plan", "solo")

    # Plan-aware size mapping
    _PLAN_SIZE = {
        "solo": "s-2vcpu-4gb",
        "pro": "s-2vcpu-8gb",
        "hosted": "s-2vcpu-4gb",  # legacy grandfathered
        "trial": "s-2vcpu-4gb",
    }

    if plan in ("solo", "pro", "hosted"):
        if not _CONCERTO_DO_API_TOKEN:
            raise HTTPException(
                status_code=503,
                detail="Hosted provisioning unavailable: CONCERTO_DO_API_TOKEN not configured",
            )
        plan_size = _PLAN_SIZE.get(plan, _HOSTED_SIZE)
        await db.update_buyer(
            req.token, status="provisioning", region=req.region, vps_size=plan_size
        )
        asyncio.create_task(
            _provision_async(
                req.token,
                _CONCERTO_DO_API_TOKEN,
                req.region,
                plan_size,
                mode=plan,  # mode is now plan name for downstream tagging
            )
        )
    elif plan == "byoc":
        if not req.do_api_key:
            raise HTTPException(
                status_code=422,
                detail="do_api_key is required for BYOC plan",
            )
        await db.update_buyer(
            req.token, status="provisioning", region=req.region, vps_size=req.size
        )
        asyncio.create_task(
            _provision_async(req.token, req.do_api_key, req.region, req.size, mode="byoc")
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plan: {plan}",
        )

    return {"status": "provisioning", "token": req.token, "plan": plan}


async def _fetch_cloud_init_logs(vps_ip: str, ssh_key_path: str) -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ssh",
            "-i", ssh_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"root@{vps_ip}",
            "tail -n 50 /var/log/cloud-init-output.log 2>/dev/null || echo 'log unavailable'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=20)
        return stdout.decode(errors="replace")
    except Exception as exc:
        return f"SSH log fetch failed: {exc}"


async def _cloud_init_timeout_watch(
    token: str, droplet_id: str, vps_ip: str, ssh_key_path: str, customer_email: str
) -> None:
    await asyncio.sleep(_CLOUD_INIT_TIMEOUT_S)
    buyer = await db.get_buyer(token)
    if not buyer or buyer["status"] != "installing":
        return

    logs = await _fetch_cloud_init_logs(vps_ip, ssh_key_path)
    log_tail = logs[-1000:] if len(logs) > 1000 else logs
    logger.error("Cloud-init timeout for token %.8s. Log tail: %s", token, log_tail)

    await db.update_buyer(
        token,
        status="failed_install",
        failure_reason=f"Cloud-init timed out after 8 min. Log: {log_tail[:500]}",
    )

    try:
        from concerto.refunds import refund
        await refund(token, "Cloud-init install timed out after 8 minutes")
    except Exception as exc:
        logger.error("Auto-refund failed for timed-out token %.8s: %s", token, exc)

    await send_operator_alert(
        f"Cloud-init timeout — token {token[:8]}",
        f"Droplet {droplet_id} on {vps_ip} timed out.\nLog tail:\n{log_tail}",
    )


def _queue_tunnel_escalation(token: str) -> None:
    try:
        entry = (
            f"\n\n## Pending: Cloudflared tunnel failure — {time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"- **Token**: {token[:8]}...\n"
            f"- **Issue**: Cloudflared quick tunnel failed after 3 retries\n"
            f"- **Action required**: SSH into droplet and manually configure tunnel or "
            f"re-provision. Notify customer once resolved.\n"
        )
        with open(_MANAGER_STATE_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass


async def _provision_async(
    token: str, do_api_key: str, region: str, size: str, mode: str = "byoc"
) -> None:
    buyer = await db.get_buyer(token)
    customer_email = buyer["email"] if buyer else ""

    try:
        droplet_id, vps_ip, ssh_key_path, ttyd_password = await provisioner.provision_droplet(
            do_api_key=do_api_key,
            region=region,
            size=size,
            token=token,
            customer_email=customer_email,
            mode=mode,
        )
    except provisioner.DOAuthError:
        await db.update_buyer(
            token, status="api_key_invalid",
            failure_reason="DigitalOcean API token is invalid or expired (401)"
        )
        return
    except provisioner.DOCreditError:
        await db.update_buyer(
            token, status="account_no_credit",
            failure_reason="DigitalOcean account has insufficient credit (402)"
        )
        return
    except provisioner.DropletBootError as exc:
        await db.update_buyer(
            token, status="provisioning_failed", failure_reason=str(exc)
        )
        try:
            from concerto.refunds import refund
            await refund(token, f"Droplet boot failed: {exc}")
        except Exception as ref_exc:
            logger.error("Auto-refund failed for boot-failed token %.8s: %s", token, ref_exc)
        return
    except TimeoutError as exc:
        await db.update_buyer(
            token, status="provisioning_timeout", failure_reason=str(exc)
        )
        try:
            from concerto.refunds import refund
            await refund(token, "Droplet provisioning timed out after 5 minutes")
        except Exception as ref_exc:
            logger.error("Auto-refund failed for timeout token %.8s: %s", token, ref_exc)
        return
    except Exception as exc:
        await db.update_buyer(
            token, status="provisioning_failed",
            failure_reason=f"{type(exc).__name__}: {str(exc)[:200]}"
        )
        return

    await db.update_buyer(
        token,
        vps_id=droplet_id,
        vps_ip=vps_ip,
        ssh_keypair_private_path=ssh_key_path,
        ttyd_password=ttyd_password,
        status="installing",
        provisioned_at=int(time.time()),
    )
    asyncio.create_task(
        _cloud_init_timeout_watch(token, droplet_id, vps_ip, ssh_key_path, customer_email)
    )


@router.post("/api/internal/droplet-ready")
async def droplet_ready(payload: DropletReadyPayload, request: Request):
    buyer = await db.get_buyer(payload.token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Token not found")

    # Verify X-Callback-Secret. Prefer the dedicated callback_secret field (new rows);
    # fall back to ttyd_password for legacy rows where callback_secret is NULL.
    # Skip the check entirely when neither field is populated yet (race at the very
    # start of install — same graceful behaviour as before).
    stored_secret = buyer.get("callback_secret") or buyer.get("ttyd_password") or ""
    incoming_secret = request.headers.get("X-Callback-Secret", "")
    if stored_secret and not hmac.compare_digest(stored_secret, incoming_secret):
        raise HTTPException(status_code=403, detail="Invalid callback secret")

    current_status = buyer.get("status", "")

    # Idempotent: already past installing — 200 no-op
    _PAST_INSTALLING = {
        "awaiting_oauth", "active", "trial_expired", "trial_upgraded",
        "cancelled", "refunded", "suspended",
    }
    if current_status in _PAST_INSTALLING:
        # Container is restarting with possibly-fresh tunnel URL AND bearer token.
        # Steady-state restart: bearer is unchanged (NF persists env) → no-op update.
        # Re-provision restart: bearer is fresh → DB must learn it or every /mcp
        # call hits 401 because the proxy + dashboard would still use the stale
        # value. Update mcp_url, ttyd_public_url, AND bearer_token. Don't touch
        # status or other plan-state fields.
        if payload.mcp_url and payload.mcp_url != "tunnel_failed":
            updates: dict = {"mcp_url": payload.mcp_url}
            if payload.ttyd_url:
                updates["ttyd_public_url"] = payload.ttyd_url
            if payload.bearer_token:
                updates["bearer_token"] = payload.bearer_token
            updates["installed_at"] = int(time.time())
            await db.update_buyer(payload.token, **updates)
            return {"ok": True, "noop": True, "mcp_url_refreshed": True}
        return {"ok": True, "noop": True}

    # Reject if not in a provisioning-in-progress state
    if current_status not in ("installing", "provisioning", "provisioning_failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Unexpected buyer status for droplet-ready callback: {current_status}",
        )

    # Cloudflared tunnel failed after retries — escalate to operator
    if payload.mcp_url == "tunnel_failed":
        _queue_tunnel_escalation(payload.token)
        await send_operator_alert(
            f"Cloudflared tunnel failed — token {payload.token[:8]}",
            f"Droplet provisioned but tunnel URL capture failed after 3 retries.\n"
            "Token: " + str(payload.token) + "\nDroplet IP: " + str(buyer.get("vps_ip", "unknown")),
        )
        await db.update_buyer(
            payload.token,
            status="provisioning_failed",
            failure_reason="Cloudflared tunnel URL capture failed — operator notified",
        )
        return {"ok": True, "escalated": True}

    await db.update_buyer(
        payload.token,
        mcp_url=payload.mcp_url,
        bearer_token=payload.bearer_token,
        ttyd_public_url=payload.ttyd_url,
        status="awaiting_oauth",
        installed_at=int(time.time()),
    )

    # For trial buyers: send ready email at awaiting_oauth (moved from trial_router.py)
    if buyer.get("plan") == "trial":
        try:
            from concerto.email_templates import trial_ready
            from concerto.email_utils import send_email
            email = buyer.get("email", "")
            dashboard_url = f"{_FRONTEND_URL}/dashboard/{payload.token}"
            expires_at = buyer.get("expires_at", 0)
            duration_seconds = max(60, int(expires_at - time.time())) if expires_at else 1800
            tpl = trial_ready(dashboard_url=dashboard_url, email=email, duration_seconds=duration_seconds)
            await send_email(email, tpl["subject"], tpl.get("html") or tpl["text"])
        except Exception:
            logger.exception("trial_ready email failed for token %.8s", payload.token)

    return {"ok": True}
