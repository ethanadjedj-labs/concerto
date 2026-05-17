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

from fastapi import APIRouter, HTTPException

from maestro import db

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
    key_path = buyer.get("ssh_keypair_private_path")

    if not vps_ip or not key_path:
        result: dict = {"oauth_complete": False, "claude_version": None, "reason": "vps_not_ready"}
        _cache[token] = (now + _CACHE_TTL, result)
        return result

    if not Path(key_path).exists():
        result = {"oauth_complete": False, "claude_version": None, "reason": "key_file_missing"}
        _cache[token] = (now + _CACHE_TTL, result)
        return result

    result = await _ssh_check(vps_ip, key_path)
    _cache[token] = (now + _CACHE_TTL, result)
    return result
