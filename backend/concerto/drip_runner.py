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
    (3,  "drip_day_3_sent_at",  lambda b: "Try this: spawn 3 sessions in parallel", "day_3_advanced_pattern", False),
    (7,  "drip_day_7_sent_at",  lambda b: "One week in — how's it going?", "day_7_check_in", False),
    (14, "drip_day_14_sent_at", lambda b: "Your subscription renews in 16 days", "day_14_renewal_preview", False),
    (21, "drip_day_21_sent_at", lambda b: "5 things power users do with Concerto", "day_21_use_case_inspiration", False),
    (30, "drip_day_30_sent_at", lambda b: "30 days in — one quick question", "day_30_one_month", False),
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
            "SELECT * FROM concerto_buyers WHERE paid_at IS NOT NULL AND email IS NOT NULL"
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
