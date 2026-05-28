import os
import time

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from concerto import db
from concerto.email_utils import send_email, send_operator_alert

router = APIRouter()

_STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
_CONCERTO_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")


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
        # Always expose the buyer's mcp_url directly. For NF the container
        # runs a cloudflared quick tunnel and writes the trycloudflare URL
        # here, so Claude.ai talks to the same hostname end-to-end (Host
        # header pass-through is required for OAuth issuer consistency).
        resp["mcp_url"] = buyer["mcp_url"]
    if buyer.get("bearer_token"):
        resp["bearer_token"] = buyer["bearer_token"]
    if status == "awaiting_oauth":
        resp["dashboard_ready_url"] = f"https://concerto.run/dashboard/{token}"

    # Hosted-only subscription fields
    if buyer.get("plan") == "hosted":
        resp["subscription_status"] = buyer.get("subscription_status")
        resp["next_renewal_at"] = buyer.get("next_renewal_at")

    # Trial-only fields
    if buyer.get("plan") == "trial":
        resp["expires_at"] = buyer.get("expires_at")

    # Auto-pause runtime state (absent when running, 'paused' when idle-paused)
    if buyer.get("runtime_state"):
        resp["runtime_state"] = buyer["runtime_state"]

    # Extra fields for error UX
    if buyer.get("failure_reason"):
        resp["failure_reason"] = buyer["failure_reason"]

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


class RefundRequest(BaseModel):
    email: str
    message: str = ""


@router.post("/api/refund-request")
async def refund_request(req: RefundRequest):
    """Public refund request form (homepage). No automatic refund: this
    only notifies the operator and confirms receipt to the customer. All
    refunds are then handled manually. The automatic safety-net refund on
    failed provisioning lives in provision_router and is unaffected."""
    email = (req.email or "").strip()
    message = (req.message or "").strip()[:2000]
    if "@" not in email or "." not in email.split("@")[-1] or len(email) > 254:
        raise HTTPException(status_code=400, detail="A valid email is required")

    # Notify the operator so a refund can be processed by hand.
    await send_operator_alert(
        "Refund request",
        f"From: {email}\n\nMessage:\n{message or '(no message provided)'}",
    )

    # Confirm receipt to the customer (best-effort; never fails the request).
    await send_email(
        to=email,
        subject="We received your Concerto refund request",
        html=(
            "<p>Hi,</p>"
            "<p>We've received your refund request and a human will "
            "review it shortly. We typically reply within 24 hours.</p>"
            "<p>If you need to add anything, just reply to this email or "
            "contact <a href='mailto:support@concerto.run'>"
            "support@concerto.run</a>.</p>"
            "<p>Thank you,<br/>The Concerto team</p>"
        ),
        text=(
            "Hi,\n\nWe've received your refund request and a human will "
            "review it shortly. We typically reply within 24 hours.\n\n"
            "If you need to add anything, reply to this email or contact "
            "support@concerto.run.\n\nThank you,\nThe Concerto team"
        ),
    )

    return {"ok": True, "received": True}
