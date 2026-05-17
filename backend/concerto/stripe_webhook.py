import asyncio
import logging
import os
import time
import uuid

import httpx
import stripe
from fastapi import APIRouter, HTTPException, Request

from concerto import db, provisioner
from concerto.email_utils import send_email, send_operator_alert

router = APIRouter()
logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_CONCERTO", "")
_STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
_SETUP_BASE = "https://concerto.run/setup"
_CONCERTO_DO_API_TOKEN = os.getenv("CONCERTO_DO_API_TOKEN", "")
_DO_API_BASE = "https://api.digitalocean.com/v2"
_MANAGER_STATE_PATH = "/opt/cortex/OPS/MANAGER_STATE.md"

_HOSTED_REGION = "nyc1"
_HOSTED_SIZE = "s-2vcpu-4gb"
_CANCEL_GRACE_SECONDS = 72 * 3600
_PAST_DUE_SUSPEND_DAYS = 7

stripe.api_key = _STRIPE_SECRET


# ─── Idempotency ──────────────────────────────────────────────────────────────


def _mark_processed(event_id: str, event_type: str) -> bool:
    """Insert event_id; return True if new (first time), False if duplicate."""
    conn = db._conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO stripe_processed_events "
            "(event_id, event_type, processed_at) VALUES (?, ?, ?)",
            (event_id, event_type, int(time.time())),
        )
        conn.commit()
        return conn.execute("SELECT changes()").fetchone()[0] > 0
    finally:
        conn.close()


# ─── Email helpers ────────────────────────────────────────────────────────────


async def _send_confirmation(to_email: str, token: str, plan: str) -> None:
    setup_url = f"{_SETUP_BASE}/{token}"
    if plan == "hosted":
        subject = "Welcome to Concerto Hosted — provision your workspace"
        body_extra = (
            "<p>Good news: you don't need a DigitalOcean account — "
            "we host the VPS for you. Just click below to pick a region "
            "and provision your Concerto in seconds.</p>"
        )
    else:
        subject = "Welcome to Concerto — provision your remote workspace"
        body_extra = (
            "<p>Click the link below to connect your DigitalOcean account "
            "and provision your remote Claude Code workspace.</p>"
        )
    await send_email(
        to=to_email,
        subject=subject,
        html=(
            "<p>Thanks for purchasing Concerto!</p>"
            + body_extra
            + f'<p><a href="{setup_url}" style="background:#7c3aed;color:white;'
            f'padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block">'
            f"Set up my Concerto</a></p>"
            "<p>This link is unique to your account — keep it safe.</p>"
        ),
    )


async def _send_payment_failed_email(to_email: str, day: int) -> None:
    await send_email(
        to=to_email,
        subject=f"Action required: Concerto payment failed (day {day})",
        html=(
            f"<p>Hi,</p>"
            f"<p>We were unable to process your Concerto payment (attempt day {day}).</p>"
            f"<p>Please update your payment method at "
            f'<a href="https://billing.stripe.com">billing.stripe.com</a> '
            f"to avoid suspension.</p>"
            f"<p>If payment is not resolved within 7 days, "
            f"your workspace will be suspended (not deleted — just paused).</p>"
        ),
    )


async def _send_suspended_email(to_email: str) -> None:
    await send_email(
        to=to_email,
        subject="Your Concerto workspace has been suspended",
        html=(
            "<p>Your Concerto workspace has been <strong>suspended</strong> "
            "due to a failed payment.</p>"
            "<p>Your data is safe. Update your payment method at "
            '<a href="https://billing.stripe.com">billing.stripe.com</a> '
            "to resume instantly.</p>"
        ),
    )


async def _send_resumed_email(to_email: str) -> None:
    await send_email(
        to=to_email,
        subject="Your Concerto workspace has been resumed",
        html=(
            "<p>Your Concerto payment succeeded. Your workspace is back online!</p>"
            '<p><a href="https://concerto.run/dashboard">Open my Concerto</a></p>'
        ),
    )


async def _send_cancellation_email(to_email: str, token: str) -> None:
    survey_url = f"https://concerto.run/feedback?token={token}"
    await send_email(
        to=to_email,
        subject="Your Concerto subscription has been cancelled",
        html=(
            "<p>Your Concerto subscription has been cancelled. "
            "Your workspace will remain accessible until the end of the current billing period.</p>"
            f'<p><a href="{survey_url}">Why did you cancel?</a> (one question, 10 seconds)</p>'
            "<p>You can reactivate at any time at concerto.run.</p>"
        ),
    )


# ─── DO power management ──────────────────────────────────────────────────────


async def _poweroff_droplet(droplet_id: str) -> None:
    do_key = os.getenv("DO_PROVISIONER_API_KEY", _CONCERTO_DO_API_TOKEN)
    if not do_key or not droplet_id:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(
                f"{_DO_API_BASE}/droplets/{droplet_id}/actions",
                headers={"Authorization": f"Bearer {do_key}"},
                json={"type": "power_off"},
            )
    except Exception as exc:
        logger.warning("poweroff_droplet failed for %s: %s", droplet_id, exc)


async def _poweron_droplet(droplet_id: str) -> None:
    do_key = os.getenv("DO_PROVISIONER_API_KEY", _CONCERTO_DO_API_TOKEN)
    if not do_key or not droplet_id:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(
                f"{_DO_API_BASE}/droplets/{droplet_id}/actions",
                headers={"Authorization": f"Bearer {do_key}"},
                json={"type": "power_on"},
            )
    except Exception as exc:
        logger.warning("poweron_droplet failed for %s: %s", droplet_id, exc)


# ─── MANAGER_STATE helpers ────────────────────────────────────────────────────


def _queue_dispute_alert(token: str, charge_id: str, email: str) -> None:
    try:
        entry = (
            f"\n\n## Pending: Stripe chargeback — {time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"- **Token**: {token[:8] if token else 'unknown'}...\n"
            f"- **Charge ID**: {charge_id}\n"
            f"- **Customer email**: {email}\n"
            f"- **Action required**: Review dispute in Stripe dashboard. "
            f"Gather evidence (purchase confirmation email, provisioning logs). "
            f"Respond within 7 days.\n"
        )
        with open(_MANAGER_STATE_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass


# ─── Payment failure handler ──────────────────────────────────────────────────


async def _handle_payment_failed(obj: dict) -> None:
    subscription_id = obj.get("subscription")
    if not subscription_id:
        return

    buyer = await db.get_buyer_by_subscription(subscription_id)
    if not buyer:
        return

    token = buyer["token"]
    email = buyer.get("email", "")
    now = int(time.time())
    failed_at = buyer.get("payment_failed_at")
    fail_count = (buyer.get("payment_failed_count") or 0) + 1

    day_map = {1: 1, 2: 3, 3: 5}
    day = day_map.get(fail_count, fail_count * 2 - 1)

    if not failed_at:
        failed_at = now

    await db.update_buyer(
        token, payment_failed_at=failed_at, payment_failed_count=fail_count,
        subscription_status="past_due",
    )

    if email and day in (1, 3, 5):
        await _send_payment_failed_email(email, day)

    # Suspend on day 7+
    days_since_failure = (now - failed_at) / 86400
    if days_since_failure >= _PAST_DUE_SUSPEND_DAYS and buyer.get("status") not in ("suspended", "refunded"):
        vps_id = buyer.get("vps_id", "")
        if vps_id:
            await _poweroff_droplet(vps_id)
        await db.update_buyer(token, status="suspended", suspended_at=now)
        if email:
            await _send_suspended_email(email)


# ─── Hosted provisioning helper ────────────────────────────────────────────────


async def _provision_hosted_async(token: str, region: str, customer_email: str) -> None:
    if not _CONCERTO_DO_API_TOKEN:
        await db.update_buyer(token, status="pending_operator_do_token")
        return
    try:
        droplet_id, vps_ip, ssh_key_path, ttyd_password = await provisioner.provision_droplet(
            mode="hosted",
            do_api_key=_CONCERTO_DO_API_TOKEN,
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


# ─── Webhook endpoint ─────────────────────────────────────────────────────────


@router.post("/webhooks/stripe-concerto")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not sig_header or not _WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Missing or unconfigured signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=401, detail="Invalid Stripe signature")

    event_id = event["id"]
    event_type = event["type"]

    # Idempotency guard — Stripe retries on 5xx
    if not _mark_processed(event_id, event_type):
        return {"ignored": True, "reason": "duplicate event"}

    obj = event["data"]["object"]
    metadata = obj.get("metadata") or {}

    # ── checkout.session.completed ────────────────────────────────────────
    if event_type == "checkout.session.completed":
        if metadata.get("product") != "concerto":
            return {"ignored": True, "reason": "product mismatch"}

        plan = metadata.get("plan", "byoc")
        customer_email = obj.get("customer_email") or (
            (obj.get("customer_details") or {}).get("email")
        )
        stripe_session_id = obj.get("id", "")
        stripe_customer_id = obj.get("customer") or ""
        token = str(uuid.uuid4())
        paid_at = int(time.time())

        subscription_id = obj.get("subscription")
        next_renewal_at = None
        if subscription_id:
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
        if stripe_customer_id:
            await db.update_buyer(token, stripe_customer_id=stripe_customer_id)

        if customer_email:
            await _send_confirmation(customer_email, token, plan)

    # ── invoice.payment_failed ────────────────────────────────────────────
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(obj)

    # ── invoice.paid (payment succeeded — resume if suspended) ───────────
    elif event_type == "invoice.paid":
        subscription_id = obj.get("subscription")
        if subscription_id:
            buyer = await db.get_buyer_by_subscription(subscription_id)
            if buyer and buyer.get("status") == "suspended":
                vps_id = buyer.get("vps_id", "")
                if vps_id:
                    await _poweron_droplet(vps_id)
                await db.update_buyer(
                    buyer["token"],
                    status="active",
                    suspended_at=None,
                    subscription_status="active",
                    payment_failed_at=None,
                    payment_failed_count=0,
                )
                email = buyer.get("email", "")
                if email:
                    await _send_resumed_email(email)

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
                if buyer.get("vps_id"):
                    await db.update_hosted_pool_status(
                        buyer["vps_id"], f"grace_destroy_at:{destroy_at}"
                    )
                email = buyer.get("email", "")
                if email:
                    await _send_cancellation_email(email, buyer["token"])

    # ── customer.subscription.created ────────────────────────────────────
    elif event_type == "customer.subscription.created":
        subscription_id = obj.get("id")
        if subscription_id:
            buyer = await db.get_buyer_by_subscription(subscription_id)
            if buyer:
                await db.update_buyer(
                    buyer["token"],
                    subscription_status="active",
                    next_renewal_at=obj.get("current_period_end"),
                )

    # ── charge.dispute.created (chargeback) ──────────────────────────────
    elif event_type == "charge.dispute.created":
        charge_id = obj.get("charge", "")
        buyer_token = ""
        email = ""

        conn = db._conn()
        try:
            row = conn.execute(
                "SELECT * FROM concerto_buyers WHERE stripe_customer_id = ?",
                (obj.get("customer", ""),)
            ).fetchone()
            if row:
                buyer_token = row["token"]
                email = row["email"] or ""
        finally:
            conn.close()

        _queue_dispute_alert(buyer_token, charge_id, email)
        await send_operator_alert(
            f"Chargeback filed — charge {charge_id[:12]}",
            f"Dispute ID: {obj.get('id', '')}\n"
            f"Charge: {charge_id}\n"
            f"Customer email: {email or 'unknown'}\n"
            f"Token: {buyer_token[:8] + '...' if buyer_token else 'unknown'}\n"
            f"Action: Respond within 7 days in Stripe dashboard.",
        )
        logger.warning("Chargeback filed: charge=%s dispute=%s", charge_id, obj.get("id"))

    return {"received": True, "event_type": event_type}
