import asyncio
import os
import time
import uuid

import httpx
import stripe
from fastapi import APIRouter, HTTPException, Request

from maestro import db, provisioner

router = APIRouter()

_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_MAESTRO", "")
_RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
_EMAIL_FROM = os.getenv("MAESTRO_EMAIL_FROM", os.getenv("EMAIL_FROM", "hello@maestro.run"))
_SETUP_BASE = "https://maestro.run/setup"
_MAESTRO_DO_API_TOKEN = os.getenv("MAESTRO_DO_API_TOKEN", "")

_HOSTED_REGION = "nyc1"
_HOSTED_SIZE = "s-2vcpu-4gb"
# Grace period before destroying a cancelled hosted droplet (72 hours)
_CANCEL_GRACE_SECONDS = 72 * 3600
# Past-due grace before suspending (3 days)
_PAST_DUE_GRACE_SECONDS = 3 * 24 * 3600


async def _send_confirmation(to_email: str, token: str, plan: str) -> None:
    if not _RESEND_API_KEY:
        return
    setup_url = f"{_SETUP_BASE}/{token}"
    if plan == "hosted":
        subject = "Welcome to Maestro Hosted — provision your workspace"
        body_extra = (
            "<p>Good news: you don't need a DigitalOcean account — "
            "we host the VPS for you. Just click below to pick a region "
            "and provision your Maestro in seconds.</p>"
        )
    else:
        subject = "Welcome to Maestro — provision your remote workspace"
        body_extra = (
            "<p>Click the link below to connect your DigitalOcean account "
            "and provision your remote Claude Code workspace.</p>"
        )
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {_RESEND_API_KEY}"},
            json={
                "from": _EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": (
                    "<p>Thanks for purchasing Maestro!</p>"
                    + body_extra
                    + f'<p><a href="{setup_url}">{setup_url}</a></p>'
                    "<p>This link is unique to your account — keep it safe.</p>"
                ),
            },
        )


async def _provision_hosted_async(token: str, region: str, customer_email: str) -> None:
    if not _MAESTRO_DO_API_TOKEN:
        await db.update_buyer(
            token,
            status="pending_operator_do_token",
        )
        return
    try:
        droplet_id, vps_ip, ssh_key_path, ttyd_password = await provisioner.provision_droplet(
            mode="hosted",
            do_api_key=_MAESTRO_DO_API_TOKEN,
            region=region,
            size=_HOSTED_SIZE,
            token=token,
            customer_email=customer_email,
        )
        await db.update_buyer(
            token,
            vps_id=droplet_id,
            vps_ip=vps_ip,
            ssh_keypair_private_path=ssh_key_path,
            ttyd_password=ttyd_password,
            status="installing",
            provisioned_at=int(time.time()),
        )
    except Exception as exc:
        err_msg = f"error:{type(exc).__name__}:{str(exc)[:100]}"
        await db.update_buyer(token, status=err_msg)


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

    event_type = event["type"]

    # ── checkout.session.completed ────────────────────────────────────────
    if event_type == "checkout.session.completed":
        plan = metadata.get("plan", "byoc")
        customer_email = obj.get("customer_email") or (
            (obj.get("customer_details") or {}).get("email")
        )
        stripe_session_id = obj.get("id", "")
        token = str(uuid.uuid4())
        paid_at = int(time.time())

        subscription_id = obj.get("subscription")
        next_renewal_at = None
        if subscription_id:
            # Stripe subscription created — fetch period end
            try:
                sub = stripe.Subscription.retrieve(subscription_id)
                next_renewal_at = sub.get("current_period_end")
            except Exception:
                pass

        await db.insert_buyer_with_plan(
            token=token,
            email=customer_email or "",
            stripe_session_id=stripe_session_id,
            paid_at=paid_at,
            plan=plan,
            subscription_id=subscription_id,
            subscription_status="active" if subscription_id else None,
            next_renewal_at=next_renewal_at,
        )

        if customer_email:
            await _send_confirmation(customer_email, token, plan)

        # hosted: provisioning is triggered from the setup page (region picker),
        # not here — the customer chooses region before clicking "Provision My Maestro"

    # ── customer.subscription.deleted ────────────────────────────────────
    elif event_type == "customer.subscription.deleted":
        subscription_id = obj.get("id")
        if subscription_id:
            buyer = await db.get_buyer_by_subscription(subscription_id)
            if buyer:
                destroy_at = int(time.time()) + _CANCEL_GRACE_SECONDS
                await db.update_buyer(
                    buyer["token"],
                    subscription_status="cancelled",
                    next_renewal_at=None,
                    status=f"cancel_grace_until:{destroy_at}",
                )
                # Also mark pool entry for grace destruction
                if buyer.get("vps_id"):
                    await db.update_hosted_pool_status(
                        buyer["vps_id"], f"grace_destroy_at:{destroy_at}"
                    )

    # ── invoice.payment_failed ────────────────────────────────────────────
    elif event_type == "invoice.payment_failed":
        subscription_id = obj.get("subscription")
        if subscription_id:
            buyer = await db.get_buyer_by_subscription(subscription_id)
            if buyer:
                suspend_at = int(time.time()) + _PAST_DUE_GRACE_SECONDS
                await db.update_buyer(
                    buyer["token"],
                    subscription_status="past_due",
                    status=f"past_due_suspend_at:{suspend_at}",
                )

    # ── customer.subscription.created ────────────────────────────────────
    elif event_type == "customer.subscription.created":
        subscription_id = obj.get("id")
        customer_id = obj.get("customer")
        if subscription_id and customer_id:
            next_renewal_at = obj.get("current_period_end")
            # Update buyer row if it already exists (race: may have been created above)
            buyer = await db.get_buyer_by_subscription(subscription_id)
            if buyer:
                await db.update_buyer(
                    buyer["token"],
                    subscription_status="active",
                    next_renewal_at=next_renewal_at,
                )

    return {"received": True}
