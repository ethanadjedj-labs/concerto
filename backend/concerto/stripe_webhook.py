import asyncio
import logging
import os
import time
import uuid

import httpx
import stripe
from fastapi import APIRouter, HTTPException, Request

from concerto import db, provider_factory as provisioner
from concerto.email_utils import send_email, send_operator_alert

router = APIRouter()
logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.getenv("STRIPE_CONCERTO_WEBHOOK_SECRET", "")
_STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
_SETUP_BASE = "https://concerto.run/setup"
_CONCERTO_DO_API_TOKEN = os.getenv("CONCERTO_DO_API_TOKEN", "")
_DO_API_BASE = "https://api.digitalocean.com/v2"
_MANAGER_STATE_PATH = "/opt/cortex/OPS/MANAGER_STATE.md"

_CANCEL_GRACE_SECONDS = 72 * 3600
_PAST_DUE_SUSPEND_DAYS = 7

# Plans that Concerto hosts (subscription-based)
_HOSTED_PLANS = {"solo", "pro"}

stripe.api_key = _STRIPE_SECRET


# ─── Idempotency (commit-after-success) ─────────────────────────────────────────
#
# Stripe retries any non-2xx response. We must only dedupe an event AFTER its
# side effects (buyer creation, provisioning, emails) have committed — otherwise
# a crash mid-handler permanently loses the side effect on the deduped retry.
#
# State machine on stripe_processed_events.status:
#   'processing' -> a handler has claimed the event but not finished
#   'done'       -> side effects committed; safe to dedupe future retries
#
# Concurrency: a duplicate delivery that arrives while the first is still
# 'processing' is told to retry later (HTTP 409). A 'processing' row older than
# _STALE_PROCESSING_SECONDS is assumed abandoned (process killed mid-flight) and
# is reclaimed via compare-and-swap so the event is never stuck forever.

# Outcomes of an attempt to claim an event for processing.
_CLAIM_NEW = "claimed"          # we own it; process now
_CLAIM_DONE = "duplicate"       # already fully processed; dedupe
_CLAIM_BUSY = "in_progress"     # another worker holds a fresh claim; retry later

_STALE_PROCESSING_SECONDS = 300


def _claim_event(event_id: str, event_type: str) -> str:
    """Atomically claim an event for processing.

    Returns _CLAIM_NEW (caller must process then call _mark_done),
    _CLAIM_DONE (already processed — dedupe), or _CLAIM_BUSY (concurrent
    in-flight attempt — caller should signal Stripe to retry later).
    """
    conn = db._conn()
    try:
        now = int(time.time())
        # processed_at is NOT NULL (legacy schema) — placeholder 0 until done.
        conn.execute(
            "INSERT INTO stripe_processed_events "
            "(event_id, event_type, status, processed_at, received_at, claimed_at) "
            "VALUES (?, ?, 'processing', 0, ?, ?) "
            "ON CONFLICT(event_id) DO NOTHING",
            (event_id, event_type, now, now),
        )
        conn.commit()
        if conn.execute("SELECT changes()").fetchone()[0] > 0:
            return _CLAIM_NEW

        row = conn.execute(
            "SELECT status, claimed_at FROM stripe_processed_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            # Vanished between insert and select (shouldn't happen) — retry later.
            return _CLAIM_BUSY
        if row["status"] == "done":
            return _CLAIM_DONE

        # status == 'processing'. Reclaim only if the prior claim looks abandoned.
        claimed_at = row["claimed_at"] or 0
        if now - claimed_at < _STALE_PROCESSING_SECONDS:
            return _CLAIM_BUSY
        conn.execute(
            "UPDATE stripe_processed_events SET claimed_at = ? "
            "WHERE event_id = ? AND status = 'processing' AND claimed_at = ?",
            (now, event_id, row["claimed_at"]),
        )
        conn.commit()
        if conn.execute("SELECT changes()").fetchone()[0] > 0:
            return _CLAIM_NEW
        # Lost the compare-and-swap race to another reclaimer.
        return _CLAIM_BUSY
    finally:
        conn.close()


def _mark_done(
    event_id: str, amount: int | None = None, currency: str | None = None
) -> None:
    """Commit the event as fully processed, recording paid amount/currency."""
    conn = db._conn()
    try:
        conn.execute(
            "UPDATE stripe_processed_events "
            "SET status = 'done', processed_at = ?, amount = ?, currency = ? "
            "WHERE event_id = ?",
            (int(time.time()), amount, currency, event_id),
        )
        conn.commit()
    finally:
        conn.close()


def _release_event(event_id: str) -> None:
    """Drop a failed claim so Stripe's retry can reprocess it cleanly.

    Only removes rows that never reached 'done' — never undoes a completed event.
    """
    conn = db._conn()
    try:
        conn.execute(
            "DELETE FROM stripe_processed_events "
            "WHERE event_id = ? AND status != 'done'",
            (event_id,),
        )
        conn.commit()
    finally:
        conn.close()


# ─── Email helpers ────────────────────────────────────────────────────────────


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
            f"your account will be suspended (not deleted — just paused).</p>"
            f"<p>Questions? Email support@concerto.run — a human will reply within 24 hours.</p>"
        ),
    )


async def _send_suspended_email(to_email: str) -> None:
    await send_email(
        to=to_email,
        subject="Your Concerto account has been suspended",
        html=(
            "<p>Your Concerto account has been <strong>suspended</strong> "
            "due to a failed payment.</p>"
            "<p>Your data is safe. Update your payment method at "
            '<a href="https://billing.stripe.com">billing.stripe.com</a> '
            "to resume instantly.</p>"
            "<p>Questions? Email support@concerto.run</p>"
        ),
    )


async def _send_resumed_email(to_email: str) -> None:
    await send_email(
        to=to_email,
        subject="Your Concerto account has been resumed",
        html=(
            "<p>Your Concerto payment succeeded. Your account is back online!</p>"
            '<p><a href="https://concerto.run/dashboard">Open my Concerto</a></p>'
        ),
    )


async def _send_renewal_email(to_email: str, token: str, plan: str) -> None:
    from concerto.email_templates import renewal_success
    dashboard_url = f"https://concerto.run/dashboard/{token}"
    tpl = renewal_success(dashboard_url=dashboard_url, email=to_email, plan=plan)
    await send_email(to_email, tpl["subject"], tpl["html"] or tpl["text"])


async def _send_cancellation_email(to_email: str, token: str) -> None:
    """Cancellation email that ALSO tells the user how to rescue their work
    before the workspace is removed (GitHub push or one-click export link)."""
    from concerto.email_templates import pre_expiry_warning
    buyer = await db.get_buyer(token)
    has_gh = bool(buyer and buyer.get("github_token"))
    dash = f"https://concerto.run/dashboard/{token}"
    tpl = pre_expiry_warning(dashboard_url=dash, email=to_email,
                             has_github=has_gh, context="cancel")
    await send_email(
        to=to_email,
        subject=tpl["subject"],
        html=tpl["html"] or tpl["text"],
    )


# ─── DO power management ──────────────────────────────────────────────────────


async def _poweroff_droplet(droplet_id: str) -> None:
    # Routed through provider_factory so NF (pause) and DO (power_off) both work.
    do_key = os.getenv("DO_PROVISIONER_API_KEY", _CONCERTO_DO_API_TOKEN)
    await provisioner.suspend(api_key=do_key, vps_id=droplet_id)


async def _poweron_droplet(droplet_id: str) -> None:
    # Routed through provider_factory so NF (resume) and DO (power_on) both work.
    do_key = os.getenv("DO_PROVISIONER_API_KEY", _CONCERTO_DO_API_TOKEN)
    await provisioner.resume(api_key=do_key, vps_id=droplet_id)


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


async def _provision_hosted_async(token: str, region: str, customer_email: str, plan: str = "solo") -> None:
    """Provision a managed droplet for solo or pro plan."""
    if not _CONCERTO_DO_API_TOKEN:
        await db.update_buyer(token, status="pending_operator_do_token")
        return
    # Determine droplet size from plan
    size = provisioner.PLAN_TO_SIZE.get(plan, "s-2vcpu-4gb")
    try:
        droplet_id, vps_ip, ssh_key_path, ttyd_password = await provisioner.provision_droplet(
            mode=plan,
            do_api_key=_CONCERTO_DO_API_TOKEN,
            region=region,
            size=size,
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


# ─── Event dispatch ─────────────────────────────────────────────────────────
#
# Performs the actual side effects for an event. Returns
# (response, amount, currency) where amount/currency (smallest currency unit +
# ISO code) are non-None only for revenue-bearing events, so the caller can
# record them once the work has committed. Any exception here propagates so the
# caller leaves the event un-acked and Stripe retries.


async def _dispatch_event(
    event_type: str, obj: dict, metadata: dict
) -> tuple[dict, int | None, str | None]:
    amount: int | None = None
    currency: str | None = None

    # ── checkout.session.completed ────────────────────────────────────────
    if event_type == "checkout.session.completed":
        if metadata.get("product") != "concerto":
            return {"ignored": True, "reason": "product mismatch"}, None, None

        plan = metadata.get("plan", "byoc")
        trial_token = metadata.get("trial_token", "")
        customer_email = obj.get("customer_email") or (
            (obj.get("customer_details") or {}).get("email")
        )
        stripe_session_id = obj.get("id", "")
        stripe_customer_id = obj.get("customer") or ""
        paid_at = int(time.time())
        amount = obj.get("amount_total")
        currency = obj.get("currency")

        subscription_id = obj.get("subscription")
        next_renewal_at = None
        if subscription_id:
            try:
                sub = await asyncio.to_thread(stripe.Subscription.retrieve, subscription_id)
                next_renewal_at = getattr(sub, "current_period_end", None)
            except Exception:
                pass

        # Trial upgrade: reuse the existing trial buyer row
        if trial_token:
            trial_buyer = await db.get_buyer(trial_token)
            if trial_buyer and trial_buyer.get("plan") == "trial":
                # Destroy the trial droplet + CF tunnel in the background
                trial_vps_id = trial_buyer.get("vps_id", "")
                trial_cf_tunnel = trial_buyer.get("cf_tunnel_id", "")
                if trial_vps_id and _CONCERTO_DO_API_TOKEN:
                    asyncio.create_task(provisioner.destroy_droplet(
                        _CONCERTO_DO_API_TOKEN, trial_vps_id, trial_cf_tunnel
                    ))

                await db.update_buyer(
                    trial_token,
                    plan=plan,
                    status="paid_unprovisioned",
                    stripe_session_id=stripe_session_id,
                    stripe_customer_id=stripe_customer_id or None,
                    paid_at=paid_at,
                    paid_amount=amount,
                    paid_currency=currency,
                    subscription_id=subscription_id,
                    subscription_status="active" if subscription_id else None,
                    next_renewal_at=next_renewal_at,
                    expires_at=None,
                    # Reset provisioning state for fresh setup
                    vps_id=None,
                    vps_ip=None,
                    mcp_url=None,
                    bearer_token=None,
                    provisioned_at=None,
                    installed_at=None,
                )
                token = trial_token

                # Send trial converted email
                from concerto.email_templates import trial_converted
                if customer_email:
                    setup_url = f"{_SETUP_BASE}/{trial_token}"
                    tpl = trial_converted(setup_url=setup_url, email=customer_email, plan=plan)
                    await send_email(customer_email, tpl["subject"], tpl["html"] or tpl["text"])
                    # Immediate J0 drip — don't wait for the hourly timer
                    from concerto.drip_runner import send_immediate_drip
                    asyncio.create_task(asyncio.to_thread(send_immediate_drip, trial_token, 0))
                return {"ok": True, "trial_upgraded": True, "token": token}, amount, currency

        # Standard (non-trial) purchase: create fresh buyer row
        token = str(uuid.uuid4())
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
        buyer_updates: dict = {}
        if stripe_customer_id:
            buyer_updates["stripe_customer_id"] = stripe_customer_id
        if amount is not None:
            buyer_updates["paid_amount"] = amount
            buyer_updates["paid_currency"] = currency
        if buyer_updates:
            await db.update_buyer(token, **buyer_updates)

        if customer_email:
            from concerto.email_templates import trial_converted
            setup_url = f"{_SETUP_BASE}/{token}"
            if plan not in _HOSTED_PLANS:
                logger.warning("Unexpected non-hosted plan=%s for customer=%s", plan, customer_email)
            else:
                tpl = trial_converted(setup_url=setup_url, email=customer_email, plan=plan)
                asyncio.create_task(send_email(customer_email, tpl["subject"], tpl["html"] or tpl["text"]))
                # Immediate J0 drip — don't wait for the hourly timer
                from concerto.drip_runner import send_immediate_drip
                asyncio.create_task(asyncio.to_thread(send_immediate_drip, token, 0))

    # ── invoice.payment_failed ────────────────────────────────────────────
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(obj)

    # ── invoice.paid (payment succeeded — resume if suspended, confirm renewal) ─
    elif event_type == "invoice.paid":
        subscription_id = obj.get("subscription")
        billing_reason = obj.get("billing_reason", "")
        amount = obj.get("amount_paid")
        currency = obj.get("currency")
        if subscription_id:
            buyer = await db.get_buyer_by_subscription(subscription_id)
            if buyer:
                email = buyer.get("email", "")
                if amount is not None:
                    await db.update_buyer(
                        buyer["token"], paid_amount=amount, paid_currency=currency
                    )
                if buyer.get("status") == "suspended":
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
                    if email:
                        await _send_resumed_email(email)
                elif billing_reason == "subscription_cycle" and email:
                    # Normal monthly/annual renewal for an active subscriber.
                    # checkout.session.completed already handles first payment.
                    await _send_renewal_email(email, buyer["token"], buyer.get("plan", ""))

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

    return {"received": True, "event_type": event_type}, amount, currency


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
    except (AttributeError, KeyError, ValueError) as exc:
        # Stripe SDK ≥15 raises AttributeError on malformed payloads missing top-level 'object'
        raise HTTPException(status_code=400, detail=f"Malformed webhook payload: {exc}")

    event_id = event["id"]
    event_type = event["type"]

    # Commit-after-success idempotency: claim the event, run side effects, and
    # mark it done ONLY once they commit. On failure we release the claim and
    # return non-2xx so Stripe retries (no side effect is ever silently lost).
    claim = _claim_event(event_id, event_type)
    if claim == _CLAIM_DONE:
        return {"ignored": True, "reason": "duplicate event"}
    if claim == _CLAIM_BUSY:
        # A concurrent delivery holds a fresh claim. Ask Stripe to retry later;
        # by then the other attempt is either done (deduped) or released.
        raise HTTPException(status_code=409, detail="Event processing in progress")

    obj_raw = event["data"]["object"]
    # Stripe SDK returns StripeObject. Use proper recursive dict conversion.
    if hasattr(obj_raw, "to_dict"):
        obj = obj_raw.to_dict()
    else:
        obj = dict(obj_raw) if hasattr(obj_raw, "keys") else obj_raw
    metadata = obj.get("metadata") or {}

    try:
        response, amount, currency = await _dispatch_event(event_type, obj, metadata)
    except Exception:
        _release_event(event_id)
        raise

    _mark_done(event_id, amount, currency)
    return response
