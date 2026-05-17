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


def welcome_after_first_session(*, email: str) -> dict:
    subject = "You're running Claude Code on your own machine"
    text = f"""\
Hi,

You just completed your first Concerto session. That means Claude Code ran a real task on your dedicated Droplet — files persisted, network was live, and nothing hit a context wall.

A few things worth knowing now that you're up:

1. Sessions persist. You can start a task, close the browser, and come back — Claude Code keeps going.

2. Use the Concerto Custom Style in claude.ai. It tells Claude to treat MCP tools as the primary execution surface and skip the narration. Grab it here: https://concerto.run/docs/custom-style

3. Reply to this email if you have questions or want to share what you built — we read every reply.

4. Your Droplet is yours. SSH in if you want, install whatever you need, or leave it as-is and let Claude handle it.

Let us know how it's going.

— The Concerto team
"""
    html = _load_html("welcome_after_first_session")
    if html:
        html = html.replace("{{email}}", email)
    return {"subject": subject, "text": text, "html": html}
