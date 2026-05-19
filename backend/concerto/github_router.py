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
import hmac
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from concerto import db

router = APIRouter()
logger = logging.getLogger(__name__)

_GITHUB_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "")
_GITHUB_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "")
_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")
_FRONTEND_URL = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")

# A GitHub OAuth App registers exactly ONE callback URL, so it cannot carry
# the per-buyer {token}; the token travels in the OAuth `state` param.
_STATIC_REDIRECT_URI = f"{_API_BASE}/api/github/callback"


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
    auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={_GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={token}"
        # `repo` is broad; `public_repo` covers the common case (clone/push
        # public repos). Private-repo users can still paste a PAT. Narrower
        # scope = less scary GitHub consent screen = higher conversion.
        "&scope=public_repo"
    )
    return RedirectResponse(url=auth_url, status_code=302)


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
    return "connected"


@router.get("/api/github/callback")
async def github_callback_static(request: Request):
    """The one registered GitHub callback. Buyer token comes from `state`."""
    query = dict(request.query_params)
    code = query.get("code", "")
    token = query.get("state", "")  # state == buyer token (set in /connect)

    if not token:
        # Nothing we can do without a token; close the popup quietly.
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
    Kept so any in-flight links still work; new flows use the static one."""
    if not _github_configured():
        return _popup_close(token, "unavailable")
    query = dict(request.query_params)
    code = query.get("code", "")
    state = query.get("state", "")
    if state != token:
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

    stored_secret = buyer.get("ttyd_password") or ""
    incoming_secret = request.headers.get("X-Callback-Secret", "")

    if not stored_secret or not hmac.compare_digest(stored_secret, incoming_secret):
        raise HTTPException(status_code=403, detail="Invalid callback secret")

    return {"github_token": buyer.get("github_token") or ""}
