"""
Tracks the first successful MCP tool call per buyer token.

GET /api/buyer/{token}/first-call-detected → {"detected": bool, "detected_at": int | null}

Call record_first_call(token) from the MCP relay when a tool call succeeds.
"""
import asyncio
import time

from fastapi import APIRouter, HTTPException

from concerto import db

router = APIRouter()

_first_calls: dict[str, int] = {}


def record_first_call(token: str) -> None:
    """Call from the MCP relay on the first successful tool call per token."""
    if token in _first_calls:
        return
    ts = int(time.time())
    _first_calls[token] = ts
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_persist(token, ts))
    except RuntimeError:
        pass


async def _persist(token: str, ts: int) -> None:
    try:
        await db.update_buyer(token, first_call_at=ts)
    except Exception:
        pass
    # Notify the operator the moment a customer starts their first work
    # (first successful tool call / build). Fires exactly once per token
    # because record_first_call() de-dupes before scheduling _persist.
    try:
        buyer = await db.get_buyer(token)
        email = (buyer or {}).get("email") or "unknown"
        plan = (buyer or {}).get("plan") or "unknown"
        from concerto.email_utils import send_operator_alert
        await send_operator_alert(
            "First build started",
            f"Customer: {email}\nPlan: {plan}\nToken: {token}\n"
            f"They just launched their first Concerto work.",
        )
    except Exception:
        pass


@router.get("/api/buyer/{token}/first-call-detected")
async def first_call_detected(token: str):
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    if token in _first_calls:
        return {"detected": True, "detected_at": _first_calls[token]}

    db_ts = buyer.get("first_call_at")
    if db_ts:
        _first_calls[token] = db_ts
        return {"detected": True, "detected_at": db_ts}

    return {"detected": False, "detected_at": None}


@router.post("/api/buyer/{token}/connector-connected")
async def connector_connected(token: str):
    """Called by the droplet's MCP server the instant the OAuth /token grant
    succeeds — i.e. the moment the user clicks Connect/Authorize in Claude.
    This is the earliest real signal we have that the connector is live, far
    sooner than the first tool call. Idempotent."""
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    record_first_call(token)
    return {"ok": True, "detected_at": _first_calls.get(token)}
