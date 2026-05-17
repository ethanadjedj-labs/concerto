"""Pre-flight validation for customer DO API keys.

Called by the BYOC setup form before redirecting to Stripe checkout.
Prevents the case where a customer pays, then we discover their DO key is invalid.
"""
import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

_DO_API_BASE = "https://api.digitalocean.com/v2"
_DO_TOKEN_RE_PREFIX = "dop_v1_"


class _PreflightRequest(BaseModel):
    do_api_key: str


@router.post("/api/preflight-do-key")
async def preflight_do_key(req: _PreflightRequest):
    """Validate a DigitalOcean API key before charging the customer.

    Returns {"ok": true, "account_email": "...", "droplet_limit": N} on success.
    Returns 400 with {"ok": false, "error": "...", "code": "..."} on failure.
    """
    key = req.do_api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail={"ok": False, "error": "API key is required", "code": "empty_key"})

    if not key.startswith(_DO_TOKEN_RE_PREFIX):
        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "error": "Invalid key format — DigitalOcean API keys start with 'dop_v1_'",
                "code": "invalid_format",
            },
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{_DO_API_BASE}/account",
                headers={"Authorization": f"Bearer {key}"},
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "error": "DigitalOcean API timed out — try again", "code": "timeout"},
        )
    except Exception as exc:
        logger.warning("DO preflight network error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "error": "Network error reaching DigitalOcean", "code": "network_error"},
        )

    if resp.status_code == 401:
        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "error": "API key rejected by DigitalOcean (401). Check that the token has read+write permissions and hasn't expired.",
                "code": "invalid_key",
            },
        )

    if resp.status_code == 403:
        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "error": "API key has insufficient permissions. Ensure it has write scope (not read-only).",
                "code": "insufficient_permissions",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "ok": False,
                "error": f"DigitalOcean returned unexpected status {resp.status_code}",
                "code": "do_error",
            },
        )

    data = resp.json().get("account", {})
    return {
        "ok": True,
        "account_email": data.get("email", ""),
        "droplet_limit": data.get("droplet_limit", 0),
        "account_status": data.get("status", ""),
    }
