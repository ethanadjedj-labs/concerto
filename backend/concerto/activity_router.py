"""Activity + resume endpoints for the auto-pause/resume lifecycle.

POST /api/internal/activity?token=<buyer-token>
    Body: {"last_active_at": <unix-float>, "ttyd_connected": <bool>}
    Called every 60 s by the MCP server heartbeat.
    Auth: token in query-string must match buyer row (low-value signal,
    no HMAC needed).

POST /api/internal/resume?token=<buyer-token>
    Wakes a paused NF service.  Idempotent: if already running returns 200.
    Polls ttyd_public_url/healthz until 200 or 60 s, then returns.
"""
from __future__ import annotations

import asyncio
import logging
import time

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from concerto import db, provider_factory as provisioner

router = APIRouter()
logger = logging.getLogger(__name__)

_RESUME_POLL_INTERVAL = 1.5   # seconds between /healthz polls
_RESUME_TIMEOUT_S = 60        # give up after this many seconds


class ActivityPayload(BaseModel):
    last_active_at: float       # unix epoch seconds
    ttyd_connected: bool = False


@router.post("/api/internal/activity")
async def record_activity(
    payload: ActivityPayload,
    token: str = Query(..., description="Buyer token"),
):
    """Heartbeat from the MCP server inside the customer container."""
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Token not found")

    # If the user has an open terminal session, treat them as active right NOW
    # regardless of the MCP-level _last_activity_ts (which may be stale because
    # the user is working in the terminal, not invoking MCP tools).
    effective_ts = int(time.time()) if payload.ttyd_connected else int(payload.last_active_at)

    await db.update_buyer(token, last_active_at=effective_ts)
    return {"ok": True}


@router.post("/api/internal/resume")
async def resume_environment(
    token: str = Query(..., description="Buyer token"),
):
    """Wake a paused NF service.  Idempotent — safe to call on a running service."""
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Token not found")

    vps_id = buyer.get("vps_id") or ""
    if not vps_id:
        raise HTTPException(status_code=409, detail="No VPS attached to this buyer")

    # Idempotent: if not paused just return OK immediately.
    if buyer.get("runtime_state") != "paused":
        return {"ok": True, "resumed": False, "note": "already running"}

    # Call provider resume (NF: POST .../resume; DO: power-on)
    await provisioner.resume(api_key="", vps_id=vps_id)

    # Clear paused state in DB
    await db.update_buyer(token, runtime_state=None)
    await db.log_lifecycle_event("resume", token, vps_id=vps_id, source="manual_resume_endpoint")

    # Poll /healthz until it responds 200 (or we time out)
    healthz_url = _build_healthz_url(buyer)
    if healthz_url:
        ready = await _poll_healthz(healthz_url)
        if not ready:
            raise HTTPException(
                status_code=504,
                detail="Service resumed but /healthz did not respond within 60 s",
            )

    logger.info("Environment resumed for token %.8s (vps_id=%s)", token, vps_id)
    return {"ok": True, "resumed": True}


def _build_healthz_url(buyer: dict) -> str | None:
    """Derive the /healthz URL from stored fields."""
    # NF services: ttyd_public_url is the public-facing URL (port 8080 via NF router)
    ttyd_url = buyer.get("ttyd_public_url") or buyer.get("mcp_url") or ""
    if not ttyd_url:
        return None
    # Strip any path suffix; healthz is at the root
    base = ttyd_url.rstrip("/").split("/mcp")[0].split("/healthz")[0]
    return f"{base}/healthz"


async def _poll_healthz(url: str) -> bool:
    """Poll url until HTTP 200 or timeout.  Returns True if successful."""
    deadline = time.monotonic() + _RESUME_TIMEOUT_S
    async with httpx.AsyncClient(timeout=5) as client:
        while time.monotonic() < deadline:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(_RESUME_POLL_INTERVAL)
    return False
