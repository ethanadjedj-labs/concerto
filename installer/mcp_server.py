#!/usr/bin/env python3
"""Concerto MCP server — runs on the customer's VPS.

FastMCP server (streamable HTTP transport, mcp>=1.2) with Bearer auth.
Listens on http://127.0.0.1:9876 (behind nginx + cloudflared tunnel).

Auth: Bearer token read from /etc/concerto/token (generated at provision time).
Session state is in-process memory; sessions are lost on restart.
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from pathlib import Path
from typing import Any

import anyio
from mcp.server.fastmcp import FastMCP

TOKEN_PATH = Path(os.environ.get("CONCERTO_TOKEN_PATH", "/etc/concerto/token"))
SESSION_DIR = Path("/var/lib/concerto/sessions")

_sessions: dict[str, dict[str, Any]] = {}


def _read_token() -> str:
    return TOKEN_PATH.read_text().strip()


mcp = FastMCP("concerto", stateless_http=True)


@mcp.tool()
async def start_claude_session(
    prompt: str,
    model: str = "claude-sonnet-4-5",
) -> dict[str, Any]:
    """Launch a `claude -p` session in the background.

    Returns {session_id, status} immediately. Poll get_claude_session() for output.
    stream-json output is captured and stored per-session (last 500 lines).
    """
    session_id = uuid.uuid4().hex[:10]
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    _sessions[session_id] = {
        "id": session_id,
        "status": "running",
        "started_at": time.time(),
        "prompt": prompt[:300],
        "model": model,
        "output_lines": [],
        "exit_code": None,
        "error": None,
    }

    task = asyncio.get_event_loop().create_task(
        _run_claude(session_id, prompt, model),
        name=f"claude-{session_id}",
    )
    _sessions[session_id]["_task"] = task
    return {"session_id": session_id, "status": "running"}


@mcp.tool()
async def list_claude_sessions() -> list[dict[str, Any]]:
    """Return all known sessions with id, status, model, and prompt preview."""
    return [
        {
            "id": s["id"],
            "status": s["status"],
            "started_at": s["started_at"],
            "model": s["model"],
            "prompt_preview": s["prompt"][:80],
        }
        for s in _sessions.values()
    ]


@mcp.tool()
async def get_claude_session(session_id: str) -> dict[str, Any]:
    """Return full output and status of a session by session_id."""
    s = _sessions.get(session_id)
    if s is None:
        return {"error": f"session {session_id!r} not found"}
    return {
        "id": s["id"],
        "status": s["status"],
        "started_at": s["started_at"],
        "model": s["model"],
        "exit_code": s.get("exit_code"),
        "error": s.get("error"),
        "output_lines": s.get("output_lines", []),
    }


@mcp.tool()
async def kill_claude_session(session_id: str) -> dict[str, Any]:
    """Cancel a running claude session (sends SIGTERM via anyio task cancellation)."""
    s = _sessions.get(session_id)
    if s is None:
        return {"error": f"session {session_id!r} not found"}
    if s["status"] != "running":
        return {"session_id": session_id, "status": s["status"], "message": "already finished"}

    task: asyncio.Task | None = s.pop("_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    s["status"] = "killed"
    return {"session_id": session_id, "status": "killed"}


async def _run_claude(session_id: str, prompt: str, model: str) -> None:
    s = _sessions[session_id]
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--model", model,
        "--no-update-check",
    ]
    try:
        result = await anyio.run_process(cmd, check=False)
        raw = result.stdout.decode("utf-8", errors="replace")
        s["output_lines"] = raw.splitlines()[-500:]
        s["exit_code"] = result.returncode
        s["status"] = "done"
    except asyncio.CancelledError:
        s["status"] = "killed"
        raise
    except Exception as exc:
        s["status"] = "failed"
        s["error"] = str(exc)
    finally:
        s.pop("_task", None)


def main() -> None:
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as _Request
    from starlette.responses import JSONResponse

    class BearerAuth(BaseHTTPMiddleware):
        async def dispatch(self, request: _Request, call_next):
            if request.url.path == "/healthz":
                return await call_next(request)
            try:
                expected = _read_token()
            except OSError:
                return JSONResponse({"error": "token file not readable"}, status_code=503)
            auth = request.headers.get("Authorization", "")
            if not auth.lower().startswith("bearer "):
                return JSONResponse({"error": "missing bearer token"}, status_code=401)
            if auth.split(" ", 1)[1].strip() != expected:
                return JSONResponse({"error": "invalid bearer token"}, status_code=401)
            return await call_next(request)

    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuth)
    uvicorn.run(app, host="127.0.0.1", port=9876, log_level="info")


if __name__ == "__main__":
    main()
