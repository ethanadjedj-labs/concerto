import asyncio
import hashlib
import hmac as _hmac
import logging
import os
import secrets
import time
from collections import defaultdict

import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from concerto import db
from concerto.email_templates import cancel_link_email
from concerto.email_utils import send_email, send_operator_alert

router = APIRouter()
logger = logging.getLogger(__name__)

_STRIPE_SECRET      = os.getenv("STRIPE_SECRET_KEY", "")
_PORTAL_RETURN_BASE = "https://concerto.run/dashboard"
_FRONTEND_BASE      = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")
_API_BASE           = "https://api.concerto.run"

# ── Cancel-link HMAC ──────────────────────────────────────────────────────────
# F-08: prefer the env-supplied secret; fall back to a per-process random so
# dev/tests work without wiring.  In prod the fallback silently invalidates
# every outstanding cancel link on every restart AND diverges across replicas
# — log a LOUD warning the moment we take the fallback path so journalctl
# surfaces the misconfiguration immediately.  Operator rotation steps live
# in docs/SECURITY_BLOCKER.md.
_CANCEL_LINK_SECRET = os.getenv("CONCERTO_CANCEL_LINK_SECRET")
if not _CANCEL_LINK_SECRET:
    _CANCEL_LINK_SECRET = secrets.token_hex(32)
    logger.warning(
        "CONCERTO_CANCEL_LINK_SECRET is not set; using a per-process random "
        "fallback. Outstanding cancel-by-email links WILL break on the next "
        "backend restart, and two replicas will diverge. Set this env var in "
        "/etc/concerto/env (see docs/SECURITY_BLOCKER.md item 2)."
    )
_CANCEL_LINK_TTL    = 3600  # 1 hour


def _sign(token: str, expires_at: int) -> str:
    msg = f"{token}:{expires_at}".encode()
    return _hmac.new(_CANCEL_LINK_SECRET.encode(), msg, hashlib.sha256).hexdigest()


def _make_cancel_link(token: str) -> str:
    expires_at = int(time.time()) + _CANCEL_LINK_TTL
    sig = _sign(token, expires_at)
    return f"{_API_BASE}/api/cancel-by-link?token={token}&expires={expires_at}&sig={sig}"


def _verify_cancel_link(token: str, expires_str: str, sig: str) -> bool:
    try:
        expires_at = int(expires_str)
    except (ValueError, TypeError):
        return False
    if time.time() > expires_at:
        return False
    expected = _sign(token, expires_at)
    return _hmac.compare_digest(expected, sig)


# ── Cancel-by-email rate limiting (in-memory, per-IP, 3/hour) ─────────────────
_CANCEL_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
_CANCEL_RATE_WINDOW = 3600
_CANCEL_RATE_MAX    = 3


def _check_and_record_attempt(ip: str) -> bool:
    now    = time.time()
    cutoff = now - _CANCEL_RATE_WINDOW
    prev   = [t for t in _CANCEL_ATTEMPTS[ip] if t > cutoff]
    if len(prev) >= _CANCEL_RATE_MAX:
        _CANCEL_ATTEMPTS[ip] = prev
        return False
    prev.append(now)
    _CANCEL_ATTEMPTS[ip] = prev
    return True


_CANCEL_ANTI_ENUM_MSG = (
    "If this email has an active subscription, you'll receive a confirmation link shortly."
)


class _PortalRequest(BaseModel):
    token: str


@router.post("/api/customer-portal-session")
async def create_customer_portal_session(req: _PortalRequest):
    buyer = await db.get_buyer(req.token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if buyer.get("plan") != "hosted":
        raise HTTPException(
            status_code=400,
            detail="Customer portal is only available for the Hosted plan",
        )

    stripe_customer_id = buyer.get("stripe_customer_id")
    if not stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "No Stripe customer ID on file yet — your subscription may still be "
                "activating. Wait a few seconds and retry, or contact support@concerto.run."
            ),
        )

    stripe.api_key = _STRIPE_SECRET
    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{_PORTAL_RETURN_BASE}/{req.token}",
        )
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"url": session.url}


class _CancelRequest(BaseModel):
    token: str
    reason: str = ""
    detail: str = ""


@router.post("/api/cancel-subscription")
async def cancel_subscription(req: _CancelRequest):
    """Smart cancel: record why, end the Stripe subscription at period end
    (user keeps access until they have paid for), notify the operator so we
    can follow up. No human gate on the cancel itself."""
    buyer = await db.get_buyer(req.token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    email = buyer.get("email") or "unknown"
    stripe_customer_id = buyer.get("stripe_customer_id")

    cancelled = False
    cancel_note = ""
    if stripe_customer_id and _STRIPE_SECRET:
        stripe.api_key = _STRIPE_SECRET
        try:
            subs = stripe.Subscription.list(
                customer=stripe_customer_id, status="active", limit=10
            )
            for sub in subs.auto_paging_iter():
                stripe.Subscription.modify(sub.id, cancel_at_period_end=True)
                cancelled = True
            if not cancelled:
                cancel_note = "no active subscription found on Stripe"
        except stripe.StripeError as exc:
            cancel_note = f"Stripe error: {exc}"
    else:
        cancel_note = "no Stripe customer on file"

    # Notify operator regardless, so we can reach out / learn why.
    await send_operator_alert(
        "Subscription cancellation",
        (
            f"Buyer: {email}\n"
            f"Token: {req.token}\n"
            f"Reason: {req.reason or '(none given)'}\n"
            f"Detail: {req.detail or '(none)'}\n"
            f"Stripe cancel applied: {cancelled}"
            + (f" ({cancel_note})" if cancel_note else "")
        ),
    )

    return {
        "cancelled": cancelled,
        "note": cancel_note,
        "message": (
            "Your subscription is set to end at the close of your current "
            "billing period — you keep access until then. We've noted your "
            "feedback and someone may reach out. Questions: "
            "support@concerto.run"
        ) if cancelled else (
            "We couldn't auto-cancel (likely no active paid subscription). "
            "We've alerted our team and will sort this out — "
            "support@concerto.run"
        ),
    }


# ── New: cancel-by-email (homepage entry point) ───────────────────────────────

class _CancelByEmailRequest(BaseModel):
    email: str


def _client_ip(request: Request) -> str:
    """F-11: real client IP for rate-limiting.

    Behind Cloudflare, `request.client.host` is a CF edge IP shared across
    many real customers — keying a per-IP bucket on it collapses to
    "one bucket per CF edge" and either lets one edge DoS legitimate users
    or makes the limit useless once CF rotates edges.  `cf-connecting-ip`
    is set and overwritten by Cloudflare on every request, so the
    customer cannot forge it through the CF front-door.  Fall back to the
    L4 peer when CF is not in the path (dev, direct hits, tests)."""
    cf = (request.headers.get("cf-connecting-ip") or "").strip()
    if cf:
        return cf
    return request.client.host if request.client else "unknown"


@router.post("/api/cancel-by-email")
async def cancel_by_email(req: _CancelByEmailRequest, request: Request):
    """Homepage cancel flow step 1: accept an email, send a one-click link.

    Always returns the same 200 response regardless of whether the email is
    found — anti-enumeration by design."""
    ip      = _client_ip(request)
    allowed = _check_and_record_attempt(ip)

    if allowed:
        email = req.email.strip().lower()
        buyer = await db.get_buyer_by_email(email)
        if buyer:
            cancel_link = _make_cancel_link(buyer["token"])
            tpl         = cancel_link_email(
                cancel_link=cancel_link, email=buyer.get("email", email)
            )
            asyncio.create_task(
                send_email(buyer.get("email", email), tpl["subject"], tpl["html"], tpl["text"])
            )

    return {"ok": True, "message": _CANCEL_ANTI_ENUM_MSG}


# ── New: cancel-by-link (one-click confirm, redirects to /cancelled) ──────────

@router.get("/api/cancel-by-link")
async def cancel_by_link(token: str, expires: str, sig: str):
    """Homepage cancel flow step 2: verify HMAC, cancel on Stripe, redirect."""
    if not _verify_cancel_link(token, expires, sig):
        raise HTTPException(status_code=400, detail="Invalid or expired cancellation link.")

    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found.")

    email              = buyer.get("email") or "unknown"
    stripe_customer_id = buyer.get("stripe_customer_id")
    cancelled          = False
    cancel_note        = ""

    if stripe_customer_id and _STRIPE_SECRET:
        stripe.api_key = _STRIPE_SECRET
        try:
            subs = stripe.Subscription.list(
                customer=stripe_customer_id, status="active", limit=10
            )
            for sub in subs.auto_paging_iter():
                stripe.Subscription.modify(sub.id, cancel_at_period_end=True)
                cancelled = True
            if not cancelled:
                cancel_note = "no active subscription found on Stripe"
        except stripe.StripeError as exc:
            cancel_note = f"Stripe error: {exc}"
    else:
        cancel_note = "no Stripe customer on file"

    await send_operator_alert(
        "Subscription cancelled via email link",
        (
            f"Buyer: {email}\n"
            f"Token: {token}\n"
            f"Stripe cancel applied: {cancelled}"
            + (f" ({cancel_note})" if cancel_note else "")
        ),
    )

    return RedirectResponse(url=f"{_FRONTEND_BASE}/cancelled", status_code=303)
