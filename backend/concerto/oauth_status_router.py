"""
GET /api/buyer/{token}/oauth-status

SSHes into the customer droplet using the stored ssh_keypair_private_path,
checks whether ~/.claude/.credentials.json exists, and returns:
  {"oauth_complete": bool, "claude_version": str | null}

Cached 30 s to avoid hammering the droplet.
"""
import asyncio
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from concerto import db

router = APIRouter()

_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 30


async def _ssh_check(vps_ip: str, key_path: str) -> dict:
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8",
        "-o", "BatchMode=yes",
        f"root@{vps_ip}",
        (
            "bash -c '"
            "if [ -f ~/.claude/.credentials.json ]; then echo FOUND; else echo MISSING; fi; "
            "claude --version 2>/dev/null || echo UNKNOWN"
            "'"
        ),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=12)
        lines = stdout.decode("utf-8", errors="replace").strip().splitlines()
        found = bool(lines) and lines[0].strip() == "FOUND"
        version_raw = lines[1].strip() if len(lines) > 1 else "UNKNOWN"
        version = None if version_raw == "UNKNOWN" else version_raw
        return {"oauth_complete": found, "claude_version": version}
    except asyncio.TimeoutError:
        return {"oauth_complete": False, "claude_version": None, "error": "ssh_timeout"}
    except Exception as exc:
        return {"oauth_complete": False, "claude_version": None, "error": str(exc)}


def _is_nf_buyer(buyer: dict) -> bool:
    return (buyer.get("vps_ip") or "").startswith("https://")


def _nf_base_url(buyer: dict) -> str:
    mcp_url = (buyer.get("mcp_url") or "").strip()
    if mcp_url.endswith("/mcp"):
        return mcp_url[:-4]
    return (buyer.get("vps_ip") or "").rstrip("/")


async def _nf_status_check(buyer: dict) -> dict:
    base_url = _nf_base_url(buyer)
    bearer = buyer.get("bearer_token", "")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{base_url}/__internal/oauth/status",
                headers={"Authorization": f"Bearer {bearer}"},
            )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "oauth_complete": data.get("oauth_complete", False),
                "claude_version": None,
                "rejected": bool(data.get("rejected")),
                "rejected_reason": data.get("rejected_reason"),
            }
    except Exception as exc:
        return {"oauth_complete": False, "claude_version": None, "error": str(exc)}
    return {"oauth_complete": False, "claude_version": None, "error": f"http_{resp.status_code}"}


@router.get("/api/buyer/{token}/oauth-status")
async def oauth_status(token: str):
    now = time.monotonic()
    if token in _cache:
        expires_at, cached = _cache[token]
        if now < expires_at:
            return cached

    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    vps_ip = buyer.get("vps_ip")
    if not vps_ip:
        result: dict = {"oauth_complete": False, "claude_version": None, "reason": "vps_not_ready"}
        _cache[token] = (now + _CACHE_TTL, result)
        return result

    if _is_nf_buyer(buyer):
        result = await _nf_status_check(buyer)
        # Don't cache a 'rejected' state — when the user clicks "Open Anthropic"
        # again to retry, we want the very next poll to see the fresh state.
        # Also shorten the TTL during NF flows; the polls are cheap.
        if not result.get("rejected"):
            _cache[token] = (now + 5, result)
        return result

    # Legacy DO path: SSH check
    key_path = buyer.get("ssh_keypair_private_path")
    if not key_path:
        result = {"oauth_complete": False, "claude_version": None, "reason": "vps_not_ready"}
        _cache[token] = (now + _CACHE_TTL, result)
        return result

    if not Path(key_path).exists():
        result = {"oauth_complete": False, "claude_version": None, "reason": "key_file_missing"}
        _cache[token] = (now + _CACHE_TTL, result)
        return result

    result = await _ssh_check(vps_ip, key_path)
    _cache[token] = (now + _CACHE_TTL, result)
    return result
