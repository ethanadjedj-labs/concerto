import os

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from concerto import db

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
