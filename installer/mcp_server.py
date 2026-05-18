#!/usr/bin/env python3
"""Concerto MCP server -- runs on the customer's VPS.

FastMCP server (streamable HTTP transport, mcp>=1.2) with OAuth 2.1 + PKCE.
Listens on http://127.0.0.1:9876 (behind nginx + cloudflared tunnel).

Auth: OAuth 2.1 Bearer tokens (issued by built-in AS) OR legacy Bearer token
      from /etc/concerto/token for backward compatibility.
Session state is in-process memory; sessions are lost on restart.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

logger = logging.getLogger("concerto.mcp")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOKEN_PATH = Path(os.environ.get("CONCERTO_TOKEN_PATH", "/etc/concerto/token"))
SESSION_DIR = Path("/var/lib/concerto/sessions")
OAUTH_DIR = Path("/var/lib/concerto")
CLIENTS_PATH = OAUTH_DIR / "oauth_clients.json"
TOKENS_PATH = OAUTH_DIR / "oauth_tokens.json"

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_sessions: dict[str, dict[str, Any]] = {}

# code -> {client_id, code_challenge, redirect_uri, expires_at}
_auth_codes: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_token() -> str:
    return TOKEN_PATH.read_text().strip()


def _base_url(request: Any) -> str:
    proto = (
        request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
        or "http"
    )
    host = (
        request.headers.get("x-forwarded-host", "").split(",")[0].strip()
        or request.headers.get("host", "localhost")
    )
    return f"{proto}://{host}"


def _pkce_verify(verifier: str, challenge: str) -> bool:
    digest = hashlib.sha256(verifier.encode()).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return computed == challenge


def _load_json(path: Path) -> dict:
    """Read a JSON store, tolerating a concurrent atomic replace.

    Writes use os.replace (atomic), so a reader either sees the old file or
    the new one - never a partial one. We still retry briefly in case the
    file is momentarily absent during the rename window, and we NEVER
    silently return {} on a parse error of a non-empty file (that used to
    mask token loss as an intermittent 401)."""
    import time as _t
    for attempt in range(5):
        try:
            if not path.exists():
                return {}
            raw = path.read_text()
            if not raw.strip():
                return {}
            return json.loads(raw)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            # Should not happen with atomic writes; brief retry then give up
            # loudly rather than silently dropping every token.
            if attempt == 4:
                logger.error("Corrupt JSON store at %s after retries", path)
                return {}
            _t.sleep(0.02)
        except OSError:
            if attempt == 4:
                return {}
            _t.sleep(0.02)
    return {}


def _save_json(path: Path, data: dict) -> None:
    """Atomically replace the JSON store.

    Write to a temp file in the same directory then os.replace() it: the
    rename is atomic on POSIX, so concurrent readers never observe a
    half-written file. This fixes the intermittent 401: /token wrote
    oauth_tokens.json non-atomically while a parallel /mcp read it mid-write,
    saw invalid JSON, and rejected a perfectly valid token."""
    import os as _os
    import tempfile as _tf
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = _tf.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with _os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(data, indent=2))
            fh.flush()
            _os.fsync(fh.fileno())
        _os.replace(tmp, str(path))
    except Exception:
        try:
            _os.unlink(tmp)
        except OSError:
            pass
        raise


def _purge_expired_codes() -> None:
    now = time.time()
    expired = [k for k, v in _auth_codes.items() if v["expires_at"] < now]
    for k in expired:
        del _auth_codes[k]


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "concerto",
    stateless_http=True,
    # FastMCP auto-enables DNS-rebinding protection when host is 127.0.0.1,
    # which 421-rejects the public tunnel Host (ce<hash>.concerto.run) on the
    # post-OAuth /mcp call -> Claude reports "Authorization failed". The server
    # is already protected by OAuth + nginx + the cloudflared tunnel, so this
    # protection is redundant here and must be disabled explicitly.
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    ),
)


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


# ---------------------------------------------------------------------------
# OAuth 2.1 endpoint handlers
# ---------------------------------------------------------------------------


async def as_metadata(request: Any) -> Any:
    """GET /.well-known/oauth-authorization-server -- RFC 8414 AS metadata."""
    from starlette.responses import JSONResponse
    base = _base_url(request)
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    })


async def pr_metadata(request: Any) -> Any:
    """GET /.well-known/oauth-protected-resource[/mcp] -- RFC 9728 resource metadata."""
    from starlette.responses import JSONResponse
    base = _base_url(request)
    return JSONResponse({
        "resource": base,
        "authorization_servers": [base],
    })


async def register(request: Any) -> Any:
    """POST /register -- RFC 7591 Dynamic Client Registration."""
    from starlette.responses import JSONResponse
    try:
        body = await request.json()
    except Exception:
        body = {}

    client_id = uuid.uuid4().hex
    now = int(time.time())
    record = dict(body)
    record["client_id"] = client_id
    record["client_id_issued_at"] = now
    record["token_endpoint_auth_method"] = "none"

    clients = _load_json(CLIENTS_PATH)
    clients[client_id] = record
    _save_json(CLIENTS_PATH, clients)

    return JSONResponse(record, status_code=201)


async def authorize(request: Any) -> Any:
    """GET /authorize -- OAuth 2.1 authorization code + PKCE (auto-approve)."""
    from starlette.responses import JSONResponse, RedirectResponse
    params = dict(request.query_params)

    client_id = params.get("client_id", "")
    redirect_uri = params.get("redirect_uri", "")
    code_challenge = params.get("code_challenge", "")
    code_challenge_method = params.get("code_challenge_method", "S256")
    response_type = params.get("response_type", "")
    state = params.get("state", "")

    # Validate required parameters
    missing = []
    if not client_id:
        missing.append("client_id")
    if not redirect_uri:
        missing.append("redirect_uri")
    if not code_challenge:
        missing.append("code_challenge")
    if response_type != "code":
        missing.append("response_type (must be 'code')")

    if missing:
        return JSONResponse(
            {"error": "invalid_request", "error_description": f"Missing or invalid: {', '.join(missing)}"},
            status_code=400,
        )

    if code_challenge_method != "S256":
        return JSONResponse(
            {"error": "invalid_request", "error_description": "Only S256 code_challenge_method is supported"},
            status_code=400,
        )

    # Validate client_id exists (allow any if registry is empty for bootstrapping)
    clients = _load_json(CLIENTS_PATH)
    if clients and client_id not in clients:
        return JSONResponse(
            {"error": "invalid_client", "error_description": f"Unknown client_id: {client_id}"},
            status_code=400,
        )

    # Auto-approve: generate code
    _purge_expired_codes()
    code = uuid.uuid4().hex + uuid.uuid4().hex
    _auth_codes[code] = {
        "client_id": client_id,
        "code_challenge": code_challenge,
        "redirect_uri": redirect_uri,
        "expires_at": time.time() + 600,
    }

    # Build redirect
    separator = "&" if "?" in redirect_uri else "?"
    location = f"{redirect_uri}{separator}code={code}"
    if state:
        location = f"{location}&state={state}"

    return RedirectResponse(url=location, status_code=302)


async def token_endpoint(request: Any) -> Any:
    """POST /token -- OAuth 2.1 token endpoint."""
    from starlette.responses import JSONResponse

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
    else:
        # form-encoded
        try:
            form = await request.form()
            body = dict(form)
        except Exception:
            body = {}

    grant_type = body.get("grant_type", "")

    if grant_type == "authorization_code":
        code = body.get("code", "")
        code_verifier = body.get("code_verifier", "")
        redirect_uri = body.get("redirect_uri", "")
        client_id = body.get("client_id", "")

        if not code or not code_verifier:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing code or code_verifier"},
                status_code=400,
            )

        _purge_expired_codes()
        stored = _auth_codes.get(code)
        if stored is None:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "Authorization code not found or expired"},
                status_code=400,
            )

        if stored["expires_at"] < time.time():
            del _auth_codes[code]
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "Authorization code expired"},
                status_code=400,
            )

        if client_id and stored["client_id"] != client_id:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "client_id mismatch"},
                status_code=400,
            )

        if redirect_uri and stored["redirect_uri"] != redirect_uri:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "redirect_uri mismatch"},
                status_code=400,
            )

        if not _pkce_verify(code_verifier, stored["code_challenge"]):
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "PKCE verification failed"},
                status_code=400,
            )

        # Consume the code
        del _auth_codes[code]

        # Issue tokens
        access_token = uuid.uuid4().hex + uuid.uuid4().hex
        refresh_token = uuid.uuid4().hex + uuid.uuid4().hex
        expires_in = 3600
        now = time.time()

        tokens = _load_json(TOKENS_PATH)
        tokens[access_token] = {
            "client_id": stored["client_id"],
            "refresh_token": refresh_token,
            "expires_at": now + expires_in,
            "scope": body.get("scope", ""),
        }
        # Also index by refresh_token for grant_type=refresh_token
        tokens[f"rt:{refresh_token}"] = {
            "client_id": stored["client_id"],
            "access_token": access_token,
            "expires_at": now + 86400 * 30,
        }
        _save_json(TOKENS_PATH, tokens)

        return JSONResponse({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
        })

    elif grant_type == "refresh_token":
        refresh_token = body.get("refresh_token", "")
        if not refresh_token:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing refresh_token"},
                status_code=400,
            )

        tokens = _load_json(TOKENS_PATH)
        rt_key = f"rt:{refresh_token}"
        rt_record = tokens.get(rt_key)

        if rt_record is None:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "refresh_token not found"},
                status_code=400,
            )

        if rt_record["expires_at"] < time.time():
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "refresh_token expired"},
                status_code=400,
            )

        # Revoke old access token if present
        old_at = rt_record.get("access_token")
        if old_at and old_at in tokens:
            del tokens[old_at]

        # Issue new access token
        new_access_token = uuid.uuid4().hex + uuid.uuid4().hex
        expires_in = 3600
        now = time.time()
        client_id = rt_record["client_id"]

        tokens[new_access_token] = {
            "client_id": client_id,
            "refresh_token": refresh_token,
            "expires_at": now + expires_in,
            "scope": "",
        }
        tokens[rt_key]["access_token"] = new_access_token

        _save_json(TOKENS_PATH, tokens)

        return JSONResponse({
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
        })

    else:
        return JSONResponse(
            {"error": "unsupported_grant_type", "error_description": f"grant_type {grant_type!r} not supported"},
            status_code=400,
        )


# ---------------------------------------------------------------------------
# App assembly
# ---------------------------------------------------------------------------

# Paths that bypass authentication entirely
_UNAUTH_EXACT = {"/healthz", "/authorize", "/register", "/token"}
_UNAUTH_PREFIXES = ("/.well-known/",)

# OAuth endpoint dispatch table: path -> (method, handler)
_OAUTH_ROUTES: dict[str, tuple[str, Any]] = {
    "/.well-known/oauth-authorization-server": ("GET", as_metadata),
    "/.well-known/oauth-protected-resource": ("GET", pr_metadata),
    "/.well-known/oauth-protected-resource/mcp": ("GET", pr_metadata),
    "/register": ("POST", register),
    "/authorize": ("GET", authorize),
    "/token": ("POST", token_endpoint),
}


def _is_unauthenticated_path(path: str) -> bool:
    if path in _UNAUTH_EXACT:
        return True
    for prefix in _UNAUTH_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _check_bearer(request: Any) -> bool:
    """Return True if the request carries a valid OAuth or legacy bearer token."""
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return False
    token = auth.split(" ", 1)[1].strip()

    # Check OAuth tokens store
    tokens = _load_json(TOKENS_PATH)
    record = tokens.get(token)
    if record is not None:
        if record.get("expires_at", 0) >= time.time():
            return True

    # Fall back to legacy static token
    try:
        expected = _read_token()
        if token == expected:
            return True
    except OSError:
        pass

    return False


class CombinedApp:
    """ASGI application that handles OAuth endpoints directly and proxies the rest to mcp_app."""

    def __init__(self, mcp_app: Any) -> None:
        self.mcp_app = mcp_app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        from starlette.requests import Request
        from starlette.responses import JSONResponse, Response

        if scope["type"] == "lifespan":
            await self.mcp_app(scope, receive, send)
            return

        if scope["type"] != "http":
            await self.mcp_app(scope, receive, send)
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        # --- OAuth / public endpoints ---
        if path in _OAUTH_ROUTES:
            expected_method, handler = _OAUTH_ROUTES[path]
            if method == expected_method:
                request = Request(scope, receive)
                response = await handler(request)
                await response(scope, receive, send)
                return
            # Method not allowed
            response = Response(status_code=405)
            await response(scope, receive, send)
            return

        # --- Health check ---
        if path == "/healthz":
            response = JSONResponse({"status": "ok"})
            await response(scope, receive, send)
            return

        # --- Auth check for all other paths ---
        request = Request(scope, receive)
        if not _check_bearer(request):
            base = _base_url(request)
            resource_meta = f"{base}/.well-known/oauth-protected-resource"
            www_auth = f'Bearer resource_metadata="{resource_meta}"'
            response = JSONResponse(
                {"error": "unauthorized", "error_description": "Valid Bearer token required"},
                status_code=401,
                headers={"WWW-Authenticate": www_auth},
            )
            await response(scope, receive, send)
            return

        # Authenticated -- forward to MCP app
        await self.mcp_app(scope, receive, send)


def main() -> None:
    import uvicorn

    mcp_app = mcp.streamable_http_app()
    app = CombinedApp(mcp_app)
    uvicorn.run(app, host="127.0.0.1", port=9876, log_level="info")


if __name__ == "__main__":
    main()
