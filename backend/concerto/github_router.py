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
from fastapi.responses import JSONResponse, RedirectResponse

from concerto import db

router = APIRouter()
logger = logging.getLogger(__name__)

_GITHUB_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "")
_GITHUB_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "")
_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")
_FRONTEND_URL = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")


def _github_configured() -> bool:
    return bool(_GITHUB_CLIENT_ID and _GITHUB_CLIENT_SECRET)


@router.get("/api/buyer/{token}/github/connect")
async def github_connect(token: str):
    """Redirect the browser to GitHub's OAuth authorization page."""
    if not _github_configured():
        return JSONResponse(
            status_code=503,
            content={"error": "github_not_configured"},
        )

    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    redirect_uri = f"{_API_BASE}/api/buyer/{token}/github/callback"
    auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={_GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={token}"
        "&scope=repo"
    )
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/api/buyer/{token}/github/callback")
async def github_callback(token: str, request: Request):
    """Exchange GitHub OAuth code for an access token and persist it."""
    if not _github_configured():
        raise HTTPException(status_code=503, detail="GitHub App not configured")

    query = dict(request.query_params)
    code = query.get("code", "")
    state = query.get("state", "")

    if state != token:
        raise HTTPException(status_code=400, detail="State mismatch")

    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    if not code:
        error = query.get("error", "access_denied")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")

    redirect_uri = f"{_API_BASE}/api/buyer/{token}/github/callback"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": _GITHUB_CLIENT_ID,
                    "client_secret": _GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
    except httpx.RequestError as exc:
        logger.exception("GitHub token exchange network error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="GitHub token exchange failed (network error)",
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub token exchange failed (HTTP {resp.status_code})",
        )

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="GitHub returned non-JSON response")

    access_token = data.get("access_token")
    if not access_token:
        gh_error = data.get("error", "unknown_error")
        logger.warning("GitHub OAuth error for token %.8s: %s", token, gh_error)
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {gh_error}")

    await db.update_buyer(token, github_token=access_token)
    logger.info("GitHub token stored for buyer %.8s", token)

    return RedirectResponse(
        url=f"{_FRONTEND_URL}/dashboard/{token}?github=connected",
        status_code=302,
    )


@router.get("/api/buyer/{token}/github/status")
async def github_status(token: str):
    """Return whether a GitHub token is stored for this buyer. No auth required."""
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return {"connected": bool(buyer.get("github_token"))}


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
