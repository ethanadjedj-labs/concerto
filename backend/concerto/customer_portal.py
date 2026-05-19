import os

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from concerto import db
from concerto.email_utils import send_operator_alert

router = APIRouter()

_STRIPE_SECRET      = os.getenv("STRIPE_SECRET_KEY", "")
_PORTAL_RETURN_BASE = "https://concerto.run/dashboard"


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
