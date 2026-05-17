import os
import time
import uuid

import httpx
import stripe
from fastapi import APIRouter, HTTPException, Request

from maestro import db

router = APIRouter()

_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_MAESTRO", "")
_RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
_EMAIL_FROM = os.getenv("MAESTRO_EMAIL_FROM", os.getenv("EMAIL_FROM", "hello@maestro.run"))
_SETUP_BASE = "https://maestro.run/setup"


async def _send_confirmation(to_email: str, token: str) -> None:
    if not _RESEND_API_KEY:
        return
    setup_url = f"{_SETUP_BASE}/{token}"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {_RESEND_API_KEY}"},
            json={
                "from": _EMAIL_FROM,
                "to": [to_email],
                "subject": "Welcome to Maestro — provision your remote workspace",
                "html": (
                    "<p>Thanks for purchasing Maestro!</p>"
                    "<p>Click the link below to connect your DigitalOcean account "
                    "and provision your remote Claude Code workspace:</p>"
                    f'<p><a href="{setup_url}">{setup_url}</a></p>'
                    "<p>This link is unique to your account — keep it safe.</p>"
                ),
            },
        )


@router.post("/webhooks/stripe-maestro")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not sig_header or not _WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Missing or unconfigured signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=401, detail="Invalid Stripe signature")

    obj = event["data"]["object"]
    metadata = obj.get("metadata") or {}
    if metadata.get("product") != "maestro":
        return {"ignored": True, "reason": "product mismatch"}

    if event["type"] == "checkout.session.completed":
        customer_email = obj.get("customer_email") or (
            (obj.get("customer_details") or {}).get("email")
        )
        stripe_session_id = obj.get("id", "")
        token = str(uuid.uuid4())
        paid_at = int(time.time())

        await db.insert_buyer(token, customer_email or "", stripe_session_id, paid_at)

        if customer_email:
            await _send_confirmation(customer_email, token)

    return {"received": True}
