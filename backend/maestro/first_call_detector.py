"""
Tracks the first successful MCP tool call per buyer token.

GET /api/buyer/{token}/first-call-detected → {"detected": bool, "detected_at": int | null}

Call record_first_call(token) from the MCP relay when a tool call succeeds.
"""
import asyncio
import time

from fastapi import APIRouter, HTTPException

from maestro import db

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
