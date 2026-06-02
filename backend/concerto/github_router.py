"""
GitHub App OAuth integration for Concerto.

Endpoints:
  GET /api/buyer/{token}/github/connect      -> redirect to GitHub OAuth
  GET /api/buyer/{token}/github/callback     -> exchange code, store token, redirect to dashboard
  GET /api/buyer/{token}/github/status       -> {"connected": bool}
  GET /api/buyer/{token}/git-credentials     -> {"github_token": str}  (VPS only, requires X-Callback-Secret)

Environment variables (all optional — feature disabled gracefully if absent):
  GITHUB_APP_CLIENT_ID      GitHub App client ID
  GITHUB_APP_CLIENT_SECRET  GitHub App client secret
  CONCERTO_API_BASE         Public base URL of this API (default: https://api.concerto.run)
  CONCERTO_FRONTEND_URL     Frontend base URL for post-auth redirect (default: https://concerto.run)
"""
import base64
import hashlib
import hmac
import logging
import os
import secrets
import time

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from concerto import db

router = APIRouter()
logger = logging.getLogger(__name__)

_README_CONTENT = """\
# Concerto workspace

This repository is your Concerto workspace.

When you use Concerto, the Claude Code agent works inside a persistent environment that is connected to this repository. Anything the agent builds for you - code, scripts, notes, configs - gets committed and pushed here automatically.

## Why this exists

- **It's yours.** You own this repo. Concerto pushes to it; you keep it.
- **Portable.** Clone it anywhere. Your work follows.
- **Visible.** Every change is in git history.

## Usage

Talk to Concerto normally. The agent will work in this repo by default. If you want to work on a different repo of yours, just ask - the agent can switch.

---

Created automatically by Concerto on first GitHub connect.
"""

_GITHUB_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "")
_GITHUB_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "")
_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")
_FRONTEND_URL = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")

# A GitHub OAuth App registers exactly ONE callback URL, so it cannot carry
# the per-buyer {token}; the token travels in the OAuth `state` param.
_STATIC_REDIRECT_URI = f"{_API_BASE}/api/github/callback"

# ── F-01 hardening: signed-state envelope for GitHub OAuth ────────────────────
#
# The `state` parameter must be opaque AND verifiable so the callback can trust
# the buyer token without re-deriving it from anything the attacker controls.
#
# Format:  base64url(nonce || expires_be8 || token_utf8) || "." || hex(hmac)
#
# Verified before the GitHub-code exchange runs.  No DB row is needed because
# the HMAC is keyed by a server-side secret (env CONCERTO_GH_STATE_SECRET,
# auto-minted at boot if unset — see the cold-start warning logged below).
_GH_STATE_TTL_S = 600  # 10 minutes; consent + redirect always fits
_GH_STATE_SECRET = os.getenv("CONCERTO_GH_STATE_SECRET")
if not _GH_STATE_SECRET:
    _GH_STATE_SECRET = secrets.token_hex(32)
    if _GITHUB_CLIENT_ID and _GITHUB_CLIENT_SECRET:
        logger.warning(
            "CONCERTO_GH_STATE_SECRET is not set; using per-process random. "
            "Outstanding GitHub OAuth flows will break on restart. "
            "Set CONCERTO_GH_STATE_SECRET in the backend env to stabilise."
        )


def _sign_state(token: str, now: int | None = None) -> str:
    """Return an opaque, signed, time-bound state string carrying `token`."""
    now = int(time.time()) if now is None else int(now)
    expires = now + _GH_STATE_TTL_S
    nonce = secrets.token_bytes(8)
    payload = nonce + expires.to_bytes(8, "big") + token.encode("utf-8")
    body = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    sig = hmac.new(
        _GH_STATE_SECRET.encode("ascii"), body.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{body}.{sig}"


def _verify_state(state: str) -> str | None:
    """Return the embedded buyer token if `state` is fresh and authentic.

    Returns None on any failure (bad shape, bad signature, expired, etc.).
    Never raises.
    """
    if not state or "." not in state:
        return None
    body, _, sig = state.rpartition(".")
    if not body or not sig:
        return None
    expected = hmac.new(
        _GH_STATE_SECRET.encode("ascii"), body.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    # Base64-decode and unpack.
    pad = "=" * (-len(body) % 4)
    try:
        payload = base64.urlsafe_b64decode(body + pad)
    except (ValueError, TypeError):
        return None
    if len(payload) < 8 + 8 + 1:
        return None
    expires = int.from_bytes(payload[8:16], "big")
    if int(time.time()) > expires:
        return None
    try:
        token = payload[16:].decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not token:
        return None
    return token


def _github_configured() -> bool:
    return bool(_GITHUB_CLIENT_ID and _GITHUB_CLIENT_SECRET)


def _popup_close(token: str, status: str) -> HTMLResponse:
    """Close the GitHub OAuth popup and notify the opener (Option B: the
    user never leaves the dashboard). If the page was somehow opened in the
    same tab (popup blocked), fall back to a normal redirect."""
    safe_status = "".join(c for c in status if c.isalnum() or c in "_-")[:32]
    html = (
        "<!doctype html><html><head><meta charset=utf-8>"
        "<title>Concerto - GitHub</title></head><body "
        "style=\"font-family:-apple-system,system-ui,sans-serif;background:"
        "#faf9f5;color:#191919;display:flex;align-items:center;"
        "justify-content:center;height:100vh;margin:0\">"
        "<p>Finishing up - you can close this window.</p>"
        "<script>(function(){var s=" + repr(safe_status) + ";"
        "try{if(window.opener&&!window.opener.closed){"
        "window.opener.postMessage({source:'concerto-github',status:s},'*');"
        "window.close();return;}}catch(e){}"
        "location.replace(" + repr(_FRONTEND_URL + "/dashboard/" + token)
        + "+'?github='+s);})();</script></body></html>"
    )
    return HTMLResponse(content=html, status_code=200)


# Back-compat alias: existing call sites use _dash(token, status).
def _dash(token: str, status: str) -> HTMLResponse:
    return _popup_close(token, status)


@router.get("/api/buyer/{token}/github/connect")
async def github_connect(token: str):
    """Redirect the browser to GitHub's OAuth authorization page."""
    if not _github_configured():
        # Dormant feature: never show a raw JSON page -- bounce back to the
        # dashboard, which renders the clean "coming soon" card.
        return _dash(token, "unavailable")

    buyer = await db.get_buyer(token)
    if not buyer:
        return _dash(token, "error")

    redirect_uri = _STATIC_REDIRECT_URI
    # F-01: state must be opaque + verifiable, NOT the raw buyer token.
    state = _sign_state(token)
    auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={_GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        # `repo` (full) scope is required: we create a private `concerto` repo
        # for the user on first connect, and MCP tools read/write private repos.
        "&scope=repo"
    )
    return RedirectResponse(url=auth_url, status_code=302)


async def _update_readme(
    client: httpx.AsyncClient,
    gh_headers: dict,
    login: str,
    repo_name: str,
) -> None:
    """Replace the auto-init README with the Concerto workspace README."""
    readme_b64 = base64.b64encode(_README_CONTENT.encode("ascii")).decode("ascii")
    sha_resp = await client.get(
        f"https://api.github.com/repos/{login}/{repo_name}/contents/README.md",
        headers=gh_headers,
    )
    put_body: dict = {
        "message": "Initialize Concerto workspace",
        "content": readme_b64,
    }
    if sha_resp.status_code == 200:
        sha = sha_resp.json().get("sha")
        if sha:
            put_body["sha"] = sha
    put_resp = await client.put(
        f"https://api.github.com/repos/{login}/{repo_name}/contents/README.md",
        headers=gh_headers,
        json=put_body,
    )
    if put_resp.status_code in (200, 201):
        logger.info("README updated for %s/%s", login, repo_name)
    else:
        logger.warning(
            "README update returned %s for %s/%s",
            put_resp.status_code, login, repo_name,
        )


async def _ensure_concerto_repo(github_token: str, buyer_token: str) -> dict:
    """Create the user's concerto home-base repo on GitHub if it does not exist.

    Idempotent: returns already_exists if the repo already belongs to the user.
    Never raises; always returns a dict with status, full_name, and login.
    """
    gh_headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Resolve the authenticated user's login.
            user_resp = await client.get(
                "https://api.github.com/user", headers=gh_headers
            )
            if user_resp.status_code != 200:
                logger.warning(
                    "GitHub /user returned %s for buyer %.8s",
                    user_resp.status_code, buyer_token,
                )
                return {"status": "error", "full_name": None, "login": None}
            login = user_resp.json().get("login")
            if not login:
                logger.warning(
                    "GitHub /user missing login for buyer %.8s", buyer_token
                )
                return {"status": "error", "full_name": None, "login": None}
            logger.info("GitHub user login=%s for buyer %.8s", login, buyer_token)

            _REPO_BODY = {
                "description": (
                    "Your Concerto workspace - work done with Claude Code lives here."
                ),
                "private": True,
                "auto_init": True,
                "license_template": None,
            }

            # Check if the primary 'concerto' repo already exists.
            primary = "concerto"
            check_resp = await client.get(
                f"https://api.github.com/repos/{login}/{primary}",
                headers=gh_headers,
            )
            if check_resp.status_code == 200:
                repo_data = check_resp.json()
                owner_login = (repo_data.get("owner") or {}).get("login", "")
                if owner_login == login:
                    full_name = repo_data.get("full_name", f"{login}/{primary}")
                    logger.info(
                        "Repo %s already exists for buyer %.8s",
                        full_name, buyer_token,
                    )
                    return {
                        "status": "already_exists",
                        "full_name": full_name,
                        "login": login,
                    }
                # Owned by someone else (e.g. a fork) - fall through to fallbacks.
                logger.info(
                    "Repo %s/%s exists with owner=%s, using fallback names",
                    login, primary, owner_login,
                )
            elif check_resp.status_code == 404:
                create_resp = await client.post(
                    "https://api.github.com/user/repos",
                    headers=gh_headers,
                    json=dict(_REPO_BODY, name=primary),
                )
                if create_resp.status_code == 201:
                    full_name = create_resp.json().get(
                        "full_name", f"{login}/{primary}"
                    )
                    logger.info(
                        "Created repo %s for buyer %.8s", full_name, buyer_token
                    )
                    await _update_readme(client, gh_headers, login, primary)
                    return {
                        "status": "created",
                        "full_name": full_name,
                        "login": login,
                    }
                elif create_resp.status_code == 422:
                    logger.warning(
                        "Create %s/%s returned 422 (conflict), using fallbacks",
                        login, primary,
                    )
                    # Fall through to fallback chain.
                else:
                    logger.warning(
                        "Create %s/%s returned %s",
                        login, primary, create_resp.status_code,
                    )
                    return {"status": "error", "full_name": None, "login": login}
            else:
                logger.warning(
                    "Check %s/%s returned %s",
                    login, primary, check_resp.status_code,
                )
                return {"status": "error", "full_name": None, "login": login}

            # Fallback chain: try workspace and then a timestamp-based name.
            fallback_names = [
                "concerto-workspace",
                f"concerto-{int(time.time())}",
            ]
            for fallback in fallback_names:
                fb_check = await client.get(
                    f"https://api.github.com/repos/{login}/{fallback}",
                    headers=gh_headers,
                )
                if fb_check.status_code == 200:
                    logger.info(
                        "Fallback %s/%s already exists, trying next",
                        login, fallback,
                    )
                    continue
                if fb_check.status_code != 404:
                    logger.warning(
                        "Fallback check %s/%s returned %s",
                        login, fallback, fb_check.status_code,
                    )
                    return {"status": "error", "full_name": None, "login": login}
                fb_create = await client.post(
                    "https://api.github.com/user/repos",
                    headers=gh_headers,
                    json=dict(_REPO_BODY, name=fallback),
                )
                if fb_create.status_code == 201:
                    full_name = fb_create.json().get(
                        "full_name", f"{login}/{fallback}"
                    )
                    logger.info(
                        "Created fallback repo %s for buyer %.8s",
                        full_name, buyer_token,
                    )
                    await _update_readme(client, gh_headers, login, fallback)
                    return {
                        "status": "fallback_used",
                        "full_name": full_name,
                        "login": login,
                    }
                if fb_create.status_code == 422:
                    logger.warning(
                        "Create fallback %s/%s returned 422, trying next",
                        login, fallback,
                    )
                    continue
                logger.warning(
                    "Create fallback %s/%s returned %s",
                    login, fallback, fb_create.status_code,
                )
                return {"status": "error", "full_name": None, "login": login}

            logger.warning(
                "All candidate repo names exhausted for buyer %.8s (login=%s)",
                buyer_token, login,
            )
            return {"status": "fallback_failed", "full_name": None, "login": login}

    except httpx.RequestError:
        logger.exception(
            "Network error in _ensure_concerto_repo for buyer %.8s", buyer_token
        )
        return {"status": "error", "full_name": None, "login": None}


async def _exchange_and_store(token: str, code: str) -> str:
    """Exchange the OAuth code, persist the GitHub token, return a status
    string for the popup ('connected' | 'error')."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": _GITHUB_CLIENT_ID,
                    "client_secret": _GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": _STATIC_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
            )
    except httpx.RequestError as exc:
        logger.exception("GitHub token exchange network error: %s", exc)
        return "error"

    if resp.status_code != 200:
        logger.warning("GitHub token exchange HTTP %s", resp.status_code)
        return "error"
    try:
        data = resp.json()
    except Exception:
        logger.warning("GitHub returned non-JSON response")
        return "error"

    access_token = data.get("access_token")
    if not access_token:
        logger.warning(
            "GitHub OAuth error for %.8s: %s",
            token, data.get("error", "unknown_error"),
        )
        return "error"

    await db.update_buyer(token, github_token=access_token)
    logger.info("GitHub token stored for buyer %.8s", token)

    # Auto-create the user's home-base repo. Must never fail the OAuth flow.
    try:
        repo_result = await _ensure_concerto_repo(access_token, token)
        repo_status = repo_result.get("status")
        full_name = repo_result.get("full_name")
        login = repo_result.get("login")
        logger.info(
            "Concerto repo for buyer %.8s: status=%s full_name=%s login=%s",
            token, repo_status, full_name, login,
        )
        if full_name:
            await db.update_buyer(token, github_concerto_repo=full_name)
        elif repo_status in ("fallback_failed", "error"):
            logger.warning(
                "Concerto repo creation did not succeed for buyer %.8s: status=%s",
                token, repo_status,
            )
        if login:
            await db.update_buyer(token, github_login=login)
    except Exception:
        logger.exception(
            "Unexpected error during repo creation for buyer %.8s", token
        )

    return "connected"


@router.get("/api/github/callback")
async def github_callback_static(request: Request):
    """The one registered GitHub callback. Buyer token is recovered from the
    signed `state` envelope (F-01 hardening — was previously the raw token,
    which let an OAuth-CSRF attacker steal the victim's GitHub access token
    onto the attacker's buyer row)."""
    query = dict(request.query_params)
    code = query.get("code", "")
    state = query.get("state", "")

    if not state:
        return _popup_close("", "error")

    token = _verify_state(state)
    if not token:
        # Unsigned/expired/forged state: refuse to look up a buyer or
        # exchange the code, because we have no proof this callback
        # belongs to a flow we started.
        logger.warning("GitHub callback rejected: bad/expired state")
        return _popup_close("", "error")

    if not _github_configured():
        return _popup_close(token, "unavailable")

    buyer = await db.get_buyer(token)
    if not buyer:
        return _popup_close(token, "error")
    if not code:
        # GitHub sends ?error=access_denied when the user clicks Cancel.
        return _popup_close(token, "cancelled")

    status = await _exchange_and_store(token, code)
    return _popup_close(token, status)


@router.get("/api/buyer/{token}/github/callback")
async def github_callback_legacy(token: str, request: Request):
    """Back-compat: old per-buyer callback path. Same logic, token from path.

    F-01 hardening: even on the legacy path, `state` must be a signed
    envelope (the new /connect emits signed state for both paths).  We
    additionally require the recovered token to match the path's token,
    so a leaked signed-state for buyer A cannot be redirected through
    buyer B's URL.
    """
    if not _github_configured():
        return _popup_close(token, "unavailable")
    query = dict(request.query_params)
    code = query.get("code", "")
    state = query.get("state", "")
    if not state:
        return _popup_close(token, "error")
    state_token = _verify_state(state)
    if not state_token or state_token != token:
        logger.warning(
            "GitHub legacy callback rejected: state mismatch for token %.8s", token
        )
        return _popup_close(token, "error")
    buyer = await db.get_buyer(token)
    if not buyer:
        return _popup_close(token, "error")
    if not code:
        return _popup_close(token, "cancelled")
    status = await _exchange_and_store(token, code)
    return _popup_close(token, status)


@router.get("/api/buyer/{token}/github/status")
async def github_status(token: str):
    """Return whether a GitHub token is stored for this buyer. No auth required."""
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    # `available` tells the UI whether GitHub OAuth is configured at all, so
    # it can present the option as "coming soon" instead of navigating the
    # user to a raw {"error":"github_not_configured"} JSON page.
    return {
        "connected": bool(buyer.get("github_token")),
        "available": bool(_GITHUB_CLIENT_ID),
    }


@router.get("/api/buyer/{token}/git-credentials")
async def git_credentials(token: str, request: Request):
    """
    VPS pull endpoint: returns the stored GitHub token if the VPS provides
    the correct X-Callback-Secret header (the buyer's ttyd_password).

    Never returns github_token without a valid secret. Unlike droplet-ready,
    we do NOT gracefully skip when stored_secret is empty — a missing
    ttyd_password means the droplet is not yet initialized.
    """
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    # Prefer the dedicated callback_secret (new rows); fall back to ttyd_password
    # for legacy rows where callback_secret is NULL (same fallback as provision_router).
    stored_secret = buyer.get("callback_secret") or buyer.get("ttyd_password") or ""
    incoming_secret = request.headers.get("X-Callback-Secret", "")

    if not stored_secret or not hmac.compare_digest(stored_secret, incoming_secret):
        raise HTTPException(status_code=403, detail="Invalid callback secret")

    return {
        "github_token": buyer.get("github_token") or "",
        "concerto_repo": buyer.get("github_concerto_repo") or "",
        "github_login": buyer.get("github_login") or "",
    }
