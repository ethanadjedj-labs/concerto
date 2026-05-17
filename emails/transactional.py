"""
Concerto transactional email templates.

Each template function returns a dict with:
    subject   : str
    text      : str  (plain-text body)
    html      : str  (HTML body, optional — None if not available)

Send via:
    from arsenal.tools.send_email_resend import send_email_resend
    tpl = purchase_confirmation(token="abc123", email="user@example.com")
    send_email_resend(to=email, subject=tpl["subject"], text=tpl["text"], html=tpl["html"])
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
    subject = "Your Concerto workspace is being prepared"
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
    subject = "Your Concerto Droplet is ready"
    text = f"""\
Hi,

Your Droplet is provisioned and the MCP tunnel is live.

Open your dashboard to grab the connector config:
{dashboard_url}

Paste the connector config into claude.ai → Settings → Connectors, then start any conversation. Claude Code is live.

If you run into anything, join our Discord: https://discord.gg/concerto

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

We hit a problem while provisioning your Droplet and couldn't complete the setup.

Reason: {reason}

You have two options:

1. Retry with a different DigitalOcean API key:
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


def trial_ready(*, dashboard_url: str, email: str, minutes: int = 30) -> dict:
    subject = f"Your Concerto trial is live — {minutes} min on the clock"
    text = f"""\
Hi,

Your free 30-minute Concerto trial workspace is ready.

Open your dashboard here:
{dashboard_url}

You have {minutes} minutes to connect claude.ai and run a real Claude Code session.
After that, the workspace is automatically destroyed.

If you want to keep going, upgrade from inside the dashboard — takes 30 seconds.

— The Concerto team
https://concerto.run
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
    subject = "Your Concerto trial ended — upgrade to keep going"
    text = f"""\
Hi,

Your 30-minute Concerto trial has ended and the workspace has been destroyed.

Want to keep going? Upgrade here:
{upgrade_url}

Options:
  Hosted — $39/month (we host the workspace, zero setup)
  BYOC   — $99 once  (your DigitalOcean account)

Questions? Reply to this email.

— The Concerto team
"""
    html = _load_html("trial_expired")
    if html:
        html = (
            html.replace("{{upgrade_url}}", upgrade_url)
            .replace("{{email}}", email)
        )
    return {"subject": subject, "text": text, "html": html}


def trial_converted(*, setup_url: str, email: str, plan: str = "hosted") -> dict:
    plan_name = {"hosted": "Concerto Hosted", "byoc": "Concerto BYOC"}.get(plan, "Concerto")
    subject = f"Welcome to {plan_name} — provisioning your workspace"
    text = f"""\
Hi,

Your payment is confirmed. Welcome to {plan_name}.

We're spinning up your workspace now. Open the link below when provisioning is done:
{setup_url}

The workspace will be ready in about 3 minutes.

— The Concerto team
"""
    html = _load_html("trial_converted")
    if html:
        html = (
            html.replace("{{setup_url}}", setup_url)
            .replace("{{email}}", email)
            .replace("{{plan_name}}", plan_name)
        )
    return {"subject": subject, "text": text, "html": html}


def welcome_after_first_session(*, email: str, discord_url: str = "https://discord.gg/concerto") -> dict:
    subject = "You're running Claude Code on your own machine"
    text = f"""\
Hi,

You just completed your first Concerto session. That means Claude Code ran a real task on your dedicated Droplet — files persisted, network was live, and nothing hit a context wall.

A few things worth knowing now that you're up:

1. Sessions persist. You can start a task, close the browser, and come back — Claude Code keeps going.

2. Use the Concerto Custom Style in claude.ai. It tells Claude to treat MCP tools as the primary execution surface and skip the narration. Grab it here: https://concerto.run/docs/custom-style

3. Join the Discord — it's where power users share session templates, workflows, and tips:
   {discord_url}

4. Your Droplet is yours. SSH in if you want, install whatever you need, or leave it as-is and let Claude handle it.

Let us know how it's going.

— The Concerto team
"""
    html = _load_html("welcome_after_first_session")
    if html:
        html = html.replace("{{discord_url}}", discord_url).replace("{{email}}", email)
    return {"subject": subject, "text": text, "html": html}
