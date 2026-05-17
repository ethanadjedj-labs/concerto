"""Refund automation for Concerto buyers.

Eligibility rules:
  - Provisioning never succeeded (status in provisioning_failed, failed_install, api_key_invalid,
    account_no_credit, provisioning_timeout) → automatic, no questions
  - Within 14 days of purchase → automatic
  - Beyond 14 days AND provisioning succeeded → requires operator review (queued in MANAGER_STATE)

BYOC: customer keeps their DigitalOcean droplet (Concerto never owned it).
Hosted: destroy droplet via DO API on refund.
"""
import asyncio
import os
import time

import httpx
import stripe

from concerto import db
from concerto.email_utils import send_email, send_operator_alert

_STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
_DO_API_BASE = "https://api.digitalocean.com/v2"
_REFUND_WINDOW_DAYS = 14
_MANAGER_STATE_PATH = "/opt/cortex/OPS/MANAGER_STATE.md"

_FAILED_STATUSES = frozenset(
    {
        "provisioning_failed",
        "failed_install",
        "api_key_invalid",
        "account_no_credit",
        "provisioning_timeout",
    }
)


class RefundError(Exception):
    pass


class RefundNotEligible(RefundError):
    pass


def is_eligible_auto(buyer: dict) -> bool:
    if buyer.get("status") in _FAILED_STATUSES:
        return True
    paid_at = buyer.get("paid_at") or 0
    age_days = (time.time() - paid_at) / 86400
    return age_days <= _REFUND_WINDOW_DAYS


async def _destroy_hosted_droplet(droplet_id: str) -> None:
    do_key = os.getenv("CONCERTO_DO_API_TOKEN", "")
    if not do_key or not droplet_id:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.delete(
                f"{_DO_API_BASE}/droplets/{droplet_id}",
                headers={"Authorization": f"Bearer {do_key}"},
            )
    except Exception:
        pass


def _queue_operator_review(buyer_token: str, reason: str) -> None:
    try:
        entry = (
            f"\n\n## Pending: Manual refund review — {time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"- **Token**: {buyer_token[:8]}...\n"
            f"- **Reason**: {reason}\n"
            f"- **Action required**: approve or deny refund at Stripe dashboard\n"
        )
        with open(_MANAGER_STATE_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass


async def refund(buyer_token: str, reason: str, full_amount: bool = True) -> dict:
    """Issue a refund for a buyer. Raises RefundNotEligible if manual review needed."""
    buyer = await db.get_buyer(buyer_token)
    if not buyer:
        raise RefundError(f"Buyer not found: {buyer_token}")
    if buyer.get("status") == "refunded":
        raise RefundError("Already refunded")

    if not is_eligible_auto(buyer):
        _queue_operator_review(buyer_token, reason)
        await send_operator_alert(
            "Manual refund review needed",
            f"Token: {buyer_token[:8]}...\nReason: {reason}\nBuyer email: {buyer.get('email', 'unknown')}",
        )
        raise RefundNotEligible(
            "Beyond 14-day window and provisioning succeeded — operator review queued"
        )

    stripe.api_key = _STRIPE_SECRET
    refund_obj = None

    stripe_session_id = buyer.get("stripe_session_id", "")
    if stripe_session_id and _STRIPE_SECRET:
        try:
            session = stripe.checkout.Session.retrieve(stripe_session_id)
            payment_intent_id = session.payment_intent
            if payment_intent_id:
                refund_obj = stripe.Refund.create(
                    payment_intent=payment_intent_id,
                    reason="requested_by_customer",
                    metadata={"concerto_token": buyer_token, "reason": reason[:500]},
                )
        except stripe.StripeError as exc:
            raise RefundError(f"Stripe refund failed: {exc}") from exc

    if buyer.get("plan") == "hosted" and buyer.get("vps_id"):
        await _destroy_hosted_droplet(buyer["vps_id"])

    await db.update_buyer(
        buyer_token,
        status="refunded",
        refunded_at=int(time.time()),
        refund_stripe_id=refund_obj.id if refund_obj else "",
        failure_reason=reason,
    )

    email = buyer.get("email", "")
    if email:
        await send_email(
            to=email,
            subject="Your Concerto refund has been processed",
            html=(
                "<p>Hi,</p>"
                "<p>Your Concerto refund has been processed. "
                "Please allow 5–10 business days for the amount to appear on your statement.</p>"
                "<p>If you have questions, reply to this email or contact "
                "<a href='mailto:support@concerto.run'>support@concerto.run</a>.</p>"
                "<p>Thank you for trying Concerto.</p>"
            ),
        )

    return {"ok": True, "refund_id": refund_obj.id if refund_obj else None}
