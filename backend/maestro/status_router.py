import os

import stripe
from fastapi import APIRouter, HTTPException

from maestro import db

router = APIRouter()

_STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")


@router.get("/api/buyer/{token}/status")
async def buyer_status(token: str):
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    resp: dict = {"status": buyer["status"], "plan": buyer.get("plan", "byoc")}
    if buyer.get("vps_ip"):
        resp["vps_ip"] = buyer["vps_ip"]
    if buyer.get("mcp_url"):
        resp["mcp_url"] = buyer["mcp_url"]
    if buyer.get("bearer_token"):
        resp["bearer_token"] = buyer["bearer_token"]
    if buyer["status"] == "awaiting_oauth":
        resp["dashboard_ready_url"] = f"https://maestro.run/dashboard/{token}"

    # Hosted-only subscription fields
    if buyer.get("plan") == "hosted":
        resp["subscription_status"] = buyer.get("subscription_status")
        resp["next_renewal_at"] = buyer.get("next_renewal_at")

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
