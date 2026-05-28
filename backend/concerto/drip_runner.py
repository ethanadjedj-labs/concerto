"""
Concerto onboarding email drip runner — fires every hour via systemd timer.

Logic:
  For each buyer with a paid_at timestamp, check which drip emails are due
  (based on elapsed days since paid_at) and send any that haven't been sent yet.

Days schedule: 0, 1, 3, 7, 14 (hosted only), 21, 30
Tracking: drip_day_N_sent_at columns in concerto_buyers (migration 006)
Transport: Migadu SMTP via concerto.transactional.MigaduSMTPClient
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

from concerto.transactional import get_client

DB_PATH = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
FRONTEND_URL = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")

DRIP_SCHEDULE = [
    # (day_offset, column, subject_fn, template_name, hosted_only)
    (0,  "drip_day_0_sent_at",  lambda b: "Welcome to Concerto — complete your setup", "day_0_welcome", False),
    (1,  "drip_day_1_sent_at",  lambda b: "Have you tried your first session?", "day_1_first_session", False),
    (3,  "drip_day_3_sent_at",  lambda b: "Ask Concerto to parallelize", "day_3_advanced_pattern", False),
    (7,  "drip_day_7_sent_at",  lambda b: "One week in — how's it going?", "day_7_check_in", False),
]

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "emails" / "drip"


def _load_template(name: str, buyer: dict) -> str | None:
    path = _TEMPLATE_DIR / f"{name}.html"
    if not path.exists():
        return None
    html = path.read_text()
    token = buyer.get("token", "")
    email = buyer.get("email", "")
    setup_url = f"{FRONTEND_URL}/setup/{token}"
    dashboard_url = f"{FRONTEND_URL}/dashboard/{token}"
    portal_url = f"{FRONTEND_URL}/dashboard/{token}?tab=billing"
    survey_url = f"{FRONTEND_URL}/survey"
    renewal_date = "next billing cycle"  # TODO: pull from Stripe subscription

    replacements = {
        "{{setup_url}}": setup_url,
        "{{dashboard_url}}": dashboard_url,
        "{{portal_url}}": portal_url,
        "{{survey_url}}": survey_url,
        "{{renewal_date}}": renewal_date,
        "{{email}}": email,
        "{{unsubscribe_url}}": f"{FRONTEND_URL}/unsubscribe/{token}",
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    return html


def _load_text_template(name: str, buyer: dict) -> str | None:
    path = _TEMPLATE_DIR / f"{name}.txt"
    if not path.exists():
        return None
    text = path.read_text()
    token = buyer.get("token", "")
    email = buyer.get("email", "")
    setup_url = f"{FRONTEND_URL}/setup/{token}"
    dashboard_url = f"{FRONTEND_URL}/dashboard/{token}"
    replacements = {
        "{{setup_url}}": setup_url,
        "{{dashboard_url}}": dashboard_url,
        "{{email}}": email,
        "{{unsubscribe_url}}": f"{FRONTEND_URL}/unsubscribe/{token}",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def _send(to: str, subject: str, html: str, text: str | None = None) -> bool:
    try:
        get_client().send(to, subject, html, text)
        return True
    except Exception as e:
        print(f"  [error] SMTP send failed: {e}")
        return False


def run() -> None:
    now = int(time.time())
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    try:
        buyers = con.execute(
            "SELECT * FROM concerto_buyers"
            " WHERE paid_at IS NOT NULL AND email IS NOT NULL"
            " AND plan != 'trial'"
            " AND (subscription_status IS NULL OR subscription_status IN ('active', 'past_due'))"
            " AND status NOT IN ('trial_expired', 'cancelled', 'refunded')"
        ).fetchall()
    except sqlite3.OperationalError as e:
        print(f"DB error (migration 006 may not be applied): {e}")
        con.close()
        return

    print(f"drip_runner: checking {len(buyers)} paid buyer(s)")

    for row in buyers:
        buyer = dict(row)
        paid_at = buyer["paid_at"]
        email = buyer["email"]
        is_hosted = buyer.get("vps_size") and "s-" not in (buyer.get("vps_size") or "")

        for day_offset, col, subject_fn, tpl_name, hosted_only in DRIP_SCHEDULE:
            if hosted_only and not is_hosted:
                continue
            if buyer.get(col):
                continue  # already sent
            due_at = paid_at + day_offset * 86400
            if now < due_at:
                continue  # not yet

            subject = subject_fn(buyer)
            html = _load_template(tpl_name, buyer)
            if html is None:
                print(f"  [warn] template missing: {tpl_name}")
                continue

            text = _load_text_template(tpl_name, buyer)
            print(f"  → sending day_{day_offset} to {email}")
            sent = _send(email, subject, html, text)
            if sent:
                con.execute(
                    f"UPDATE concerto_buyers SET {col} = ? WHERE token = ?",
                    (now, buyer["token"]),
                )
                con.commit()


if __name__ == "__main__":
    run()


# ─────────────────────────────────────────────────────────────────────────────
# Immediate send (called from stripe_webhook on payment confirmation)
# ─────────────────────────────────────────────────────────────────────────────

def send_immediate_drip(token: str, day_offset: int) -> bool:
    """Send a specific drip email NOW for one buyer, bypassing the timer schedule.

    Used to deliver J0 (welcome) the moment a payment is confirmed, instead of
    waiting up to ~1h for the next timer tick. Returns True on success.

    Idempotent: if the drip column is already set (already sent), returns True
    without re-sending. If buyer doesn't match the eligibility filter, returns
    False and logs a warning.
    """
    # Find the schedule row for this day_offset
    schedule_row = next(
        ((d, col, subj_fn, tpl_name, hosted_only)
         for (d, col, subj_fn, tpl_name, hosted_only) in DRIP_SCHEDULE
         if d == day_offset),
        None,
    )
    if not schedule_row:
        print(f"send_immediate_drip: no schedule entry for day {day_offset}")
        return False
    _, col, subject_fn, tpl_name, hosted_only = schedule_row

    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT * FROM concerto_buyers"
            " WHERE token = ? AND paid_at IS NOT NULL AND email IS NOT NULL"
            " AND plan != 'trial'"
            " AND (subscription_status IS NULL OR subscription_status IN ('active', 'past_due'))"
            " AND status NOT IN ('trial_expired', 'cancelled', 'refunded')",
            (token,),
        ).fetchone()
    except sqlite3.OperationalError as e:
        print(f"send_immediate_drip: DB error: {e}")
        con.close()
        return False

    if not row:
        print(f"send_immediate_drip: buyer {token[:8]}... not eligible (trial/cancelled/missing)")
        con.close()
        return False

    buyer = dict(row)
    email = buyer["email"]

    if buyer.get(col):
        print(f"send_immediate_drip: day_{day_offset} already sent to {email}, skipping")
        con.close()
        return True  # idempotent: treat as success

    is_hosted = buyer.get("vps_size") and "s-" not in (buyer.get("vps_size") or "")
    if hosted_only and not is_hosted:
        print(f"send_immediate_drip: day_{day_offset} is hosted-only, buyer is not hosted")
        con.close()
        return False

    subject = subject_fn(buyer)
    html = _load_template(tpl_name, buyer)
    if html is None:
        print(f"send_immediate_drip: template {tpl_name} missing")
        con.close()
        return False
    text = _load_text_template(tpl_name, buyer)

    print(f"send_immediate_drip: → sending day_{day_offset} to {email} (immediate)")
    sent = _send(email, subject, html, text)
    if sent:
        try:
            con.execute(
                f"UPDATE concerto_buyers SET {col} = ? WHERE token = ?",
                (int(time.time()), buyer["token"]),
            )
            con.commit()
        except Exception as e:
            print(f"send_immediate_drip: DB mark failed: {e}")
    con.close()
    return sent
