import os
import time

import stripe
from fastapi import APIRouter, HTTPException

from concerto import db
from concerto.refunds import RefundError, RefundNotEligible, is_eligible_auto

router = APIRouter()

_STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")


@router.get("/api/buyer/{token}/status")
async def buyer_status(token: str):
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    status = buyer["status"]
    resp: dict = {"status": status, "plan": buyer.get("plan", "byoc")}

    if buyer.get("vps_ip"):
        resp["vps_ip"] = buyer["vps_ip"]
    if buyer.get("mcp_url"):
        resp["mcp_url"] = buyer["mcp_url"]
    if buyer.get("bearer_token"):
        resp["bearer_token"] = buyer["bearer_token"]
    if status == "awaiting_oauth":
        resp["dashboard_ready_url"] = f"https://concerto.run/dashboard/{token}"

    # Hosted-only subscription fields
    if buyer.get("plan") == "hosted":
        resp["subscription_status"] = buyer.get("subscription_status")
        resp["next_renewal_at"] = buyer.get("next_renewal_at")

    # Extra fields for error UX
    if buyer.get("failure_reason"):
        resp["failure_reason"] = buyer["failure_reason"]

    # Refund eligibility (visible for 14 days)
    paid_at = buyer.get("paid_at") or 0
    age_days = (time.time() - paid_at) / 86400
    resp["refund_eligible"] = is_eligible_auto(buyer)
    resp["refund_window_open"] = age_days <= 14

    # Dashboard opened tracking
    if status in ("awaiting_oauth", "active"):
        if not buyer.get("dashboard_opened_at"):
            await db.update_buyer(token, dashboard_opened_at=int(time.time()))

    return resp


@router.post("/api/buyer/{token}/cancel")
async def cancel_subscription(token: str):
    """Cancel the Stripe subscription for a hosted buyer."""
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if buyer.get("plan") != "hosted":
        raise HTTPException(status_code=400, detail="Not a hosted plan")

    subscription_id = buyer.get("subscription_id")
    if not subscription_id:
        raise HTTPException(status_code=400, detail="No subscription found")

    if not _STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    stripe.api_key = _STRIPE_SECRET_KEY
    try:
        stripe.Subscription.cancel(subscription_id)
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    await db.update_buyer(token, subscription_status="cancelling")
    return {"cancelled": True}


@router.post("/api/buyer/{token}/refund")
async def request_refund(token: str):
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    from concerto.refunds import refund
    try:
        result = await refund(token, reason="Customer requested via dashboard")
        return result
    except RefundNotEligible as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "refund_not_eligible", "message": str(exc)},
        )
    except RefundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
