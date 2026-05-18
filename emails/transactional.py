"""
Concerto transactional email templates.

Each template function returns a dict with:
    subject   : str
    text      : str  (plain-text body)
    html      : str | None  (HTML body — None if template file missing)

Send via:
    from backend.concerto.email_utils import send_email   (async)
    from backend.concerto.transactional import get_client  (sync)
"""

from __future__ import annotations

import os
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_html(name: str) -> str | None:
    path = _TEMPLATE_DIR / f"{name}.html"
    if path.exists():
        return path.read_text()
    return None


def purchase_confirmation(*, token: str, email: str) -> dict:
    setup_url = f"https://concerto.run/setup/{token}"
    subject = "Your Concerto order is confirmed"
    text = f"""\
Hi,

Thanks for purchasing Concerto. Your order is confirmed.

Complete your setup here:
{setup_url}

The link expires in 48 hours. If anything goes wrong, reply to this email — we're fast.

— The Concerto team
https://concerto.run
"""
    html = _load_html("purchase_confirmation")
    if html:
        html = html.replace("{{setup_url}}", setup_url).replace("{{email}}", email)
    return {"subject": subject, "text": text, "html": html}


def provisioning_complete(*, dashboard_url: str, email: str) -> dict:
    subject = "Your Concerto is live"
    text = f"""\
Hi,

Your Concerto account is provisioned and the MCP tunnel is live.

Open your dashboard to grab the connector config:
{dashboard_url}

Paste the connector config into claude.ai → Settings → Connectors, then start any conversation. Claude Code is live.

Questions? Reply to this email — a human responds within 24 hours.

— The Concerto team
"""
    html = _load_html("provisioning_complete")
    if html:
        html = html.replace("{{dashboard_url}}", dashboard_url).replace("{{email}}", email)
    return {"subject": subject, "text": text, "html": html}


def provisioning_failed(*, reason: str, refund_url: str, retry_url: str, email: str) -> dict:
    subject = "Concerto setup failed — refund available"
    text = f"""\
Hi,

We hit a problem getting your account ready and couldn't complete the setup.

Reason: {reason}

You have two options:

1. Retry setup:
   {retry_url}

2. Request a full refund (no questions asked):
   {refund_url}

We're sorry for the trouble. If you want to understand what went wrong or need help, reply to this email.

— The Concerto team
"""
    html = _load_html("provisioning_failed")
    if html:
        html = (
            html.replace("{{reason}}", reason)
            .replace("{{refund_url}}", refund_url)
            .replace("{{retry_url}}", retry_url)
            .replace("{{email}}", email)
        )
    return {"subject": subject, "text": text, "html": html}


def welcome_after_first_session(*, email: str) -> dict:
    subject = "Your first Concerto session is done"
    text = f"""\
Hi,

You just completed your first Concerto session. Claude Code ran a real task on your account — files persisted, network was live, and nothing hit a context wall.

A few things worth knowing now that you're up:

1. Sessions persist. You can start a task, close the browser, and come back — Claude Code keeps going.

2. Use the Concerto Custom Style in claude.ai. It tells Claude to treat MCP tools as the primary execution surface and skip the narration. Grab it here: https://concerto.run/docs/custom-style

3. Reply to this email if you have questions or want to share what you built — we read every reply.

Let us know how it's going.

— The Concerto team
https://concerto.run | support@concerto.run
"""
    html = _load_html("welcome_after_first_session")
    if html:
        html = html.replace("{{email}}", email)
    return {"subject": subject, "text": text, "html": html}


def trial_ready(*, dashboard_url: str, email: str, minutes: int = 30) -> dict:
    subject = "Your Concerto trial is live"
    text = f"""\
Hi,

Your 30-minute Concerto trial is ready. You have {minutes} minutes to try it.

Open your dashboard and grab the connector config:
{dashboard_url}

Steps:
1. Open the dashboard above
2. Paste the connector config into claude.ai → Settings → Connectors
3. Start any conversation — Claude Code is live

After {minutes} minutes your trial ends automatically.
If you want to keep going, upgrade from inside the dashboard (30 seconds).

— The Concerto team
https://concerto.run | support@concerto.run
"""
    html = _load_html("trial_ready")
    if html:
        html = (
            html.replace("{{dashboard_url}}", dashboard_url)
            .replace("{{email}}", email)
            .replace("{{minutes}}", str(minutes))
        )
    return {"subject": subject, "text": text, "html": html}


def trial_expired(*, upgrade_url: str, email: str) -> dict:
    subject = "Your Concerto trial just ended"
    text = f"""\
Hi,

Your 30-minute Concerto trial just ended.

To keep using Concerto, subscribe below — you'll get a fresh environment provisioned in about 5 minutes:

- Solo: $49/month
- Pro: $99/month (parallel runs)

Upgrade here: {upgrade_url}

Questions? Reply to this email — a human responds fast.

— The Concerto team
https://concerto.run | support@concerto.run
"""
    html = _load_html("trial_expired")
    if html:
        html = (
            html.replace("{{upgrade_url}}", upgrade_url)
            .replace("{{email}}", email)
        )
    return {"subject": subject, "text": text, "html": html}


def trial_converted(*, setup_url: str, email: str, plan_name: str = "Concerto") -> dict:
    subject = f"Welcome to {plan_name} — your environment is being set up"
    text = f"""\
Hi,

Your payment is confirmed. We're setting up your account — it'll be ready in about 5 minutes.

Open your dashboard when it's ready:
{setup_url}

Steps:
1. Open the dashboard above
2. Copy the connector config into claude.ai → Settings → Connectors
3. Start any conversation — Claude Code is live

You tried it for free and decided it was worth it — that's the whole idea. Welcome to the full experience.

— The Concerto team
https://concerto.run | support@concerto.run
"""
    html = _load_html("trial_converted")
    if html:
        html = (
            html.replace("{{setup_url}}", setup_url)
            .replace("{{email}}", email)
            .replace("{{plan_name}}", plan_name)
        )
    return {"subject": subject, "text": text, "html": html}
