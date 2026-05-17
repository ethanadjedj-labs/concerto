#!/usr/bin/env python3
"""
Test Migadu SMTP health for concerto.run.

Usage:
    python ops/scripts/test_email_send.py

Sends a test email to adjedjethan@gmail.com (OPERATOR_EMAIL) and exits with:
  0 — sent successfully
  1 — SMTP failure (check error message for details)
  2 — env vars missing (SMTP not configured yet)

Also queries the Migadu API to report the current domain validation state.
Run from /opt/concerto/ with the concerto venv or any Python 3.11+ interpreter.
"""

import os
import sys
import smtplib
import ssl
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

REQUIRED_VARS = [
    "CONCERTO_SMTP_HOST",
    "CONCERTO_SMTP_PORT",
    "CONCERTO_SMTP_USER_NOREPLY",
    "CONCERTO_SMTP_PASS_NOREPLY",
    "CONCERTO_EMAIL_FROM",
    "CONCERTO_EMAIL_REPLY_TO",
]


def _check_env() -> bool:
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}")
        print("Load /etc/cortex/env first:  source /etc/cortex/env")
        return False
    return True


def _query_migadu_domain_state() -> str:
    """Returns domain state from Migadu API, or 'unknown' if API call fails."""
    api_user = os.getenv("MIGADU_API_USER", "")
    api_key  = os.getenv("MIGADU_API_KEY", "")
    if not api_user or not api_key:
        return "unknown (MIGADU_API_USER or MIGADU_API_KEY not set)"
    try:
        import urllib.request, base64
        domain = "concerto.run"
        url = f"https://api.migadu.com/v1/domains/{domain}"
        creds = base64.b64encode(f"{api_user}:{api_key}".encode()).decode()
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            state    = data.get("state", "?")
            can_send = data.get("can_send", "?")
            can_recv = data.get("can_receive", "?")
            return f"state={state} can_send={can_send} can_receive={can_recv}"
    except Exception as exc:
        return f"unknown (API error: {exc})"


def main() -> int:
    print("=== Concerto SMTP health test ===\n")

    if not _check_env():
        return 2

    host     = os.environ["CONCERTO_SMTP_HOST"]
    port     = int(os.environ["CONCERTO_SMTP_PORT"])
    user     = os.environ["CONCERTO_SMTP_USER_NOREPLY"]
    password = os.environ["CONCERTO_SMTP_PASS_NOREPLY"]
    from_    = os.environ["CONCERTO_EMAIL_FROM"]
    reply_to = os.environ["CONCERTO_EMAIL_REPLY_TO"]
    to       = os.getenv("OPERATOR_EMAIL", "adjedjethan@gmail.com")

    print(f"  SMTP host:  {host}:{port} (STARTTLS)")
    print(f"  From:       {from_}")
    print(f"  Reply-To:   {reply_to}")
    print(f"  To:         {to}")

    print("\n  Querying Migadu domain state... ", end="", flush=True)
    domain_state = _query_migadu_domain_state()
    print(domain_state)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[Concerto] SMTP health check — test send"
    msg["From"]    = f"Concerto <{from_}>"
    msg["Reply-To"] = reply_to
    msg["To"]      = to
    msg["Date"]    = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="concerto.run")

    text_body = (
        "This is a Concerto SMTP health check sent via Migadu (smtp.migadu.com:587 STARTTLS).\n\n"
        f"If you received this, Migadu SMTP for concerto.run is working.\n\n"
        f"Domain state at test time: {domain_state}\n"
    )
    html_body = f"""\
<html><body style="font-family:monospace;background:#0d0d0d;color:#e8e8e8;padding:24px;">
<h2 style="color:#d97757">Concerto SMTP health check</h2>
<p>This is a test send via Migadu (smtp.migadu.com:587 STARTTLS).</p>
<p>If you received this, outbound email for concerto.run is working.</p>
<p style="color:#888">Domain state at test time: {domain_state}</p>
</body></html>"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print("\n  Connecting to SMTP...", end=" ", flush=True)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls(context=ctx)
            s.login(user, password)
            s.send_message(msg)
        print("OK")
        print(f"\n  SUCCESS — message {msg['Message-ID']} sent to {to}")
        print(f"  Domain state: {domain_state}")
        return 0
    except smtplib.SMTPAuthenticationError as exc:
        print("FAILED")
        print(f"\n  AUTH ERROR: {exc}")
        if "inactive" in domain_state or "can_send=False" in domain_state:
            print("  Domain is inactive — Migadu hasn't validated DNS yet.")
            print("  Wait 5–60 min and retry. Check: app.migadu.com → Domains → concerto.run")
        else:
            print("  Check CONCERTO_SMTP_USER_NOREPLY / CONCERTO_SMTP_PASS_NOREPLY in /etc/cortex/env")
        print(f"  Domain state: {domain_state}")
        return 1
    except smtplib.SMTPException as exc:
        print("FAILED")
        print(f"\n  SMTP ERROR: {exc}")
        if "inactive" in str(exc).lower() or "not found" in str(exc).lower():
            print("  Migadu domain may still be validating DNS — wait 5–60 min and retry.")
        print(f"  Domain state: {domain_state}")
        return 1
    except OSError as exc:
        print("FAILED")
        print(f"\n  NETWORK ERROR: {exc}")
        print("  Is port 587 outbound blocked by the firewall? (Hetzner blocks 465 but not 587)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
