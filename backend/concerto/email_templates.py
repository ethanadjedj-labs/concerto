"""Concerto transactional email builders.

Each function returns a dict: {subject: str, html: str, text: str}
Send via concerto.email_utils.send_email (async) or concerto.transactional.get_client (sync).

Brand tokens: bg #faf9f5, card #ffffff, divider #f3efe5, peach #cc785c,
              body #191919, muted #8a847b.
"""

from __future__ import annotations


def _html_page(title: str, body_html: str) -> str:
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8" />'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0" />'
        f"<title>{title}</title>"
        "</head>"
        '<body style="margin:0;padding:0;background:#faf9f5;'
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;"
        'color:#191919;">'
        '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        ' style="background:#faf9f5;">'
        "<tr><td align=\"center\" style=\"padding:40px 20px;\">"
        '<table width="560" cellpadding="0" cellspacing="0" border="0"'
        ' style="max-width:560px;width:100%;">'
        "<tr><td style=\"padding-bottom:24px;font-size:16px;font-weight:700;"
        'letter-spacing:.04em;color:#191919;">Concerto</td></tr>'
        "<tr><td style=\"background:#ffffff;border:1px solid #f3efe5;"
        'border-radius:8px;padding:32px;">'
        + body_html
        + "</td></tr>"
        "<tr><td style=\"padding-top:24px;font-size:12px;color:#8a847b;text-align:center;\">"
        "Concerto &middot; "
        '<a href="https://concerto.run" style="color:#8a847b;text-decoration:none;">concerto.run</a>'
        " &middot; "
        '<a href="mailto:support@concerto.run" style="color:#8a847b;text-decoration:none;">'
        "support@concerto.run</a>"
        "</td></tr>"
        "</table></td></tr></table></body></html>"
    )


def _cta(url: str, label: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:#cc785c;color:#ffffff;'
        "text-decoration:none;font-weight:600;font-size:15px;padding:12px 28px;"
        f'border-radius:6px;letter-spacing:.01em;">{label}</a>'
    )


def _steps_table(rows: str) -> str:
    return (
        '<table cellpadding="0" cellspacing="0" border="0"'
        ' style="background:#faf9f5;border:1px solid #f3efe5;border-radius:6px;'
        'padding:16px 20px;margin:0 0 24px;width:100%;box-sizing:border-box;">'
        f"<tr><td style=\"font-size:14px;color:#4a4540;line-height:2.2;\">{rows}</td></tr>"
        "</table>"
    )



def trial_ready(*, dashboard_url: str, email: str, minutes: int = 30) -> dict:
    """Sent when a trial finishes provisioning."""
    subject = "Your Concerto trial is live"
    steps = _steps_table(
        '<strong style="color:#191919;">1.</strong> Open your dashboard and grab the connector config<br>'
        '<strong style="color:#191919;">2.</strong> In claude.ai → Settings → Connectors → paste it<br>'
        '<strong style="color:#191919;">3.</strong> Start any conversation — Claude Code is live'
    )
    body_html = (
        '<p style="font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;'
        'color:#cc785c;margin:0 0 16px;">Free Trial</p>'
        '<h1 style="font-size:22px;font-weight:700;color:#191919;margin:0 0 16px;line-height:1.3;">'
        "Your trial workspace is ready.</h1>"
        f'<p style="font-size:15px;line-height:1.6;color:#4a4540;margin:0 0 20px;">'
        f"You have <strong>{minutes} minutes</strong> to try the full Concerto workspace. "
        "No card required.</p>"
        + steps
        + _cta(dashboard_url, "Open your dashboard →")
        + f'<p style="font-size:13px;color:#8a847b;margin:20px 0 0;line-height:1.5;">'
        f"After {minutes} minutes the workspace is automatically removed. "
        "To keep going, upgrade from inside the dashboard.</p>"
    )
    text = (
        f"Your Concerto trial workspace is live.\n\n"
        f"You have {minutes} minutes to try it.\n\n"
        f"Open your dashboard: {dashboard_url}\n\n"
        f"Steps:\n"
        f"1. Open the dashboard above\n"
        f"2. Paste the connector config into claude.ai → Settings → Connectors\n"
        f"3. Start any conversation — Claude Code is live\n\n"
        f"After {minutes} minutes the workspace is automatically removed.\n"
        f"To keep going, upgrade from inside the dashboard.\n\n"
        f"— The Concerto team\nhttps://concerto.run | support@concerto.run\n"
    )
    return {"subject": subject, "html": _html_page(subject, body_html), "text": text}


def trial_converted(*, setup_url: str, email: str, plan: str) -> dict:
    """Sent when a customer pays (Stripe checkout.session.completed). Highest-stakes email."""
    plan_display = plan.capitalize() if plan else "Concerto"
    subject = f"Welcome to Concerto {plan_display} — you're all set"
    steps = _steps_table(
        '<strong style="color:#191919;">1.</strong> Open your dashboard when it\'s ready<br>'
        '<strong style="color:#191919;">2.</strong> Copy the connector config into claude.ai → Settings → Connectors<br>'
        '<strong style="color:#191919;">3.</strong> Start any conversation — Claude Code is live'
    )
    body_html = (
        '<p style="font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;'
        'color:#cc785c;margin:0 0 16px;">Payment confirmed</p>'
        f'<h1 style="font-size:22px;font-weight:700;color:#191919;margin:0 0 16px;line-height:1.3;">'
        f"Welcome to {plan_display}.</h1>"
        '<p style="font-size:15px;line-height:1.6;color:#4a4540;margin:0 0 20px;">'
        "Your payment is confirmed. Your workspace is being prepared — ready in about 3 minutes.</p>"
        + steps
        + _cta(setup_url, "Open your dashboard →")
        + '<p style="font-size:13px;color:#8a847b;margin:20px 0 0;line-height:1.5;">'
        "Questions? Reply to this email — a human responds within 24 hours.</p>"
    )
    text = (
        f"Welcome to Concerto {plan_display}.\n\n"
        f"Your payment is confirmed. Your workspace is being prepared — ready in about 3 minutes.\n\n"
        f"Open your dashboard: {setup_url}\n\n"
        f"Steps:\n"
        f"1. Open the dashboard above\n"
        f"2. Copy the connector config into claude.ai → Settings → Connectors\n"
        f"3. Start any conversation — Claude Code is live\n\n"
        f"Questions? Reply to this email — a human responds within 24 hours.\n\n"
        f"— The Concerto team\nhttps://concerto.run | support@concerto.run\n"
    )
    return {"subject": subject, "html": _html_page(subject, body_html), "text": text}


def trial_expired(*, upgrade_url: str, email: str) -> dict:
    """Sent when a trial ends without conversion."""
    subject = "Your Concerto trial has ended"
    plan_rows = _steps_table(
        '<strong style="color:#191919;">Solo</strong> — $49/mo, we host the workspace<br>'
        '<strong style="color:#191919;">Pro</strong> — $99/mo for parallel runs'
    )
    body_html = (
        '<p style="font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;'
        'color:#8a847b;margin:0 0 16px;">Trial ended</p>'
        '<h1 style="font-size:22px;font-weight:700;color:#191919;margin:0 0 16px;line-height:1.3;">'
        "Your 30-minute trial has ended.</h1>"
        '<p style="font-size:15px;line-height:1.6;color:#4a4540;margin:0 0 20px;">'
        "Your trial workspace has been removed. Everything you experienced is available "
        "the moment you subscribe.</p>"
        + plan_rows
        + _cta(upgrade_url, "Subscribe →")
        + '<p style="font-size:13px;color:#8a847b;margin:20px 0 0;line-height:1.5;">'
        "Questions? Reply to this email — a human responds fast.</p>"
    )
    text = (
        f"Your Concerto trial has ended.\n\n"
        f"Your trial workspace has been removed. Everything you experienced is available "
        f"the moment you subscribe.\n\n"
        f"Subscribe to Solo — $49/mo (we host the workspace)\n"
        f"or Pro — $99/mo for parallel runs\n\n"
        f"Upgrade here: {upgrade_url}\n\n"
        f"Questions? Reply to this email — a human responds fast.\n\n"
        f"— The Concerto team\nhttps://concerto.run | support@concerto.run\n"
    )
    return {"subject": subject, "html": _html_page(subject, body_html), "text": text}


def byoc_purchase_confirmed(*, setup_url: str, email: str) -> dict:
    """Sent when a BYOC customer pays (no trial). Cream/peach, no infra vocabulary."""
    subject = "Welcome to Concerto — your account is ready"
    body_html = (
        '<p style="font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;'
        'color:#cc785c;margin:0 0 16px;">Payment confirmed</p>'
        '<h1 style="font-size:22px;font-weight:700;color:#191919;margin:0 0 16px;line-height:1.3;">'
        "Welcome to Concerto.</h1>"
        '<p style="font-size:15px;line-height:1.6;color:#4a4540;margin:0 0 20px;">'
        "Your payment is confirmed. Open the link below to complete your setup.</p>"
        + _cta(setup_url, "Complete setup →")
        + '<p style="font-size:13px;color:#8a847b;margin:20px 0 0;line-height:1.5;">'
        "Questions? Reply to this email — a human responds within 24 hours.</p>"
    )
    text = (
        "Welcome to Concerto.\n\n"
        "Your payment is confirmed. Open the link below to complete your setup.\n\n"
        f"Setup link: {setup_url}\n\n"
        "Questions? Reply to this email — a human responds within 24 hours.\n\n"
        "— The Concerto team\nhttps://concerto.run | support@concerto.run\n"
    )
    return {"subject": subject, "html": _html_page(subject, body_html), "text": text}
