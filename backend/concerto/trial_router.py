"""
Free 30-minute trial: POST /api/trial/start, GET /api/trial/eligibility.

Rate limits (DB-backed, no in-memory state):
  - 1 trial per email address, forever
  - 1 trial per IP per 24 h
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import re as _re
import secrets
import time

# Operator allowlist — these emails bypass trial-limit checks entirely (used for E2E testing)
_OPERATOR_EMAIL_RE = _re.compile(r"^(adjedjethan|zhohangir)(\+.*)?@gmail\.com$", _re.IGNORECASE)

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from concerto import db
from concerto.email_utils import send_email
from concerto.provider_factory import provision_droplet, DOAuthError, DOCreditError

router = APIRouter()
logger = logging.getLogger(__name__)

_TRIAL_DURATION_S = 30 * 60       # 30 minutes (public)
_OPERATOR_TRIAL_DURATION_S = 2 * 60 * 60   # 2 hours for whitelisted operators (filming/E2E)
_TRIAL_48H_DURATION_S = 48 * 60 * 60       # 48 hours (extended public trial)
# Whitelisted public trial durations only -- never a free-form value
# (a client must not be able to request an arbitrarily long trial).
_PUBLIC_TRIAL_DURATIONS = {
    "30min": _TRIAL_DURATION_S,
    "48h": _TRIAL_48H_DURATION_S,
}
_HOSTED_REGION    = os.getenv("CONCERTO_TRIAL_REGION", "nyc1")
_HOSTED_SIZE      = "s-2vcpu-4gb"
_DO_API_TOKEN     = os.getenv("CONCERTO_DO_API_TOKEN", "")
_FRONTEND_URL     = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


# ─── DB helpers ──────────────────────────────────────────────────────────────


async def _email_already_trialed(email: str) -> bool:
    def _run():
        conn = db._conn()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM concerto_buyers WHERE email = ? AND plan = 'trial'",
                (email.lower(),),
            ).fetchone()
            return row[0] > 0
        finally:
            conn.close()
    return await asyncio.to_thread(_run)


async def _ip_trialed_recently(ip: str) -> bool:
    cutoff = int(time.time()) - 86_400
    def _run():
        conn = db._conn()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM concerto_buyers"
                " WHERE trial_origin_ip = ? AND plan = 'trial' AND paid_at > ?",
                (ip, cutoff),
            ).fetchone()
            return row[0] > 0
        finally:
            conn.close()
    return await asyncio.to_thread(_run)


async def _insert_trial_buyer(token: str, email: str, ip: str, expires_at: int) -> None:
    now = int(time.time())
    def _run():
        conn = db._conn()
        try:
            conn.execute(
                """INSERT INTO concerto_buyers
                   (token, email, stripe_session_id, status, paid_at, plan,
                    trial_origin_ip, expires_at)
                   VALUES (?, ?, 'trial', 'provisioning', ?, 'trial', ?, ?)""",
                (token, email.lower(), now, ip, expires_at),
            )
            conn.commit()
        finally:
            conn.close()
    await asyncio.to_thread(_run)


# ─── Background provision ─────────────────────────────────────────────────────


async def _provision_trial(token: str, email: str) -> None:
    if not _DO_API_TOKEN:
        await db.update_buyer(
            token,
            status="provisioning_failed",
            failure_reason="CONCERTO_DO_API_TOKEN not configured",
        )
        logger.error("Trial provision skipped: CONCERTO_DO_API_TOKEN not set")
        return

    try:
        droplet_id, vps_ip, ssh_key_path, ttyd_password = await provision_droplet(
            do_api_key=_DO_API_TOKEN,
            region=_HOSTED_REGION,
            size=_HOSTED_SIZE,
            token=token,
            customer_email=email,
            mode="trial",
        )
    except DOAuthError as exc:
        await db.update_buyer(token, status="provisioning_failed", failure_reason=str(exc))
        return
    except DOCreditError as exc:
        await db.update_buyer(token, status="provisioning_failed", failure_reason=str(exc))
        return
    except Exception as exc:
        logger.exception("Trial provision failed for token %.8s", token)
        await db.update_buyer(
            token, status="provisioning_failed",
            failure_reason=f"{type(exc).__name__}: {str(exc)[:200]}",
        )
        return

    # Always update infra fields (vps_id, vps_ip, etc.) so status_router can serve them.
    # Only advance status to "installing" if the container hasn't already called back
    # and advanced it to "awaiting_oauth". NF containers can call back during
    # _poll_until_running, before this line runs.
    current = await db.get_buyer(token)
    current_status = (current or {}).get("status", "")
    _CALLBACK_ALREADY_ADVANCED = {"awaiting_oauth", "active", "trial_expired"}
    new_status = current_status if current_status in _CALLBACK_ALREADY_ADVANCED else "installing"
    await db.update_buyer(
        token,
        vps_id=droplet_id,
        vps_ip=vps_ip,
        ssh_keypair_private_path=ssh_key_path,
        ttyd_password=ttyd_password,
        status=new_status,
        provisioned_at=int(time.time()),
    )



# ─── Routes ───────────────────────────────────────────────────────────────────


class TrialStartRequest(BaseModel):
    email: str
    honeypot: str = ""   # must be blank
    plan: str = "30min"  # "30min" (default) or "48h"; validated server-side


@router.post("/api/trial/start", status_code=201)
async def trial_start(req: TrialStartRequest, request: Request):
    # Bot trap
    if req.honeypot:
        raise HTTPException(status_code=400, detail="invalid_request")

    email = req.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="invalid_email")

    # F-04: client-supplied X-Forwarded-For is trivially spoofable, so we
    # never trust it.  Cloudflare overwrites cf-connecting-ip with the real
    # peer; if that header is absent (local dev, direct hit) we fall back
    # to the L4 peer.  Either source is unforgeable by the HTTP client.
    client_ip = (
        request.headers.get("cf-connecting-ip", "").strip()
        or (request.client.host if request.client else "unknown")
    )

    # Rate limiting (operator allowlist bypasses both checks)
    if not _OPERATOR_EMAIL_RE.match(email):
        if await _email_already_trialed(email):
            raise HTTPException(
                status_code=409,
                detail={"error": "trial_already_used", "message": "This email has already used a free trial."},
            )
        if await _ip_trialed_recently(client_ip):
            raise HTTPException(
                status_code=429,
                detail={"error": "ip_rate_limited", "message": "Only one trial per IP per 24 hours."},
            )

    token     = secrets.token_urlsafe(32)
    _is_op = bool(_OPERATOR_EMAIL_RE.match(email))
    # Public trial duration is whitelisted; unknown value -> 30min.
    _requested = _PUBLIC_TRIAL_DURATIONS.get(req.plan, _TRIAL_DURATION_S)
    _dur = max(_OPERATOR_TRIAL_DURATION_S, _requested) if _is_op else _requested
    expires_at = int(time.time()) + _dur

    await _insert_trial_buyer(token, email, client_ip, expires_at)

    # Provision async — don't block the response
    asyncio.create_task(_provision_trial(token, email))

    dashboard_url = f"{_FRONTEND_URL}/dashboard/{token}"
    return {
        "token": token,
        "dashboard_url": dashboard_url,
        "expires_at": expires_at,
        "trial_duration_minutes": _dur // 60,
    }


@router.get("/api/trial/eligibility")
async def trial_eligibility(email: str = "", ip: str = ""):
    """F-05 hardening: the response no longer encodes whether the supplied
    email or IP has been used.  The only signal is `invalid_email` for
    obvious format errors (the trial-start form already validates this
    client-side; surfacing it here is helpful and leaks nothing).

    All other queries return the same canonical "looks fine, try it" payload.
    The real eligibility check still happens on POST /api/trial/start with
    the unforgeable peer IP — see F-04.  Probing this endpoint cannot be
    used to enumerate customers."""
    if email:
        if not _EMAIL_RE.match(email.strip()):
            return {"eligible": False, "reason": "invalid_email"}
    return {"eligible": True, "reason": ""}
