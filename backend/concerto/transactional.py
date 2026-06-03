"""Concerto transactional email client — routes through mailroom, falls back
to raw Migadu SMTP only for CRITICAL sends when mailroom is unreachable.

## Routing policy

Every send must specify a criticality:

``critical=True``  — TRANSACTIONAL CRITICAL (payment receipts, billing alerts).
    Primary path: mailroom (brand="concerto", send_kind="transactional").
    Fallback path on MailroomError: raw smtplib STARTTLS:587 — receipts must
    not block after a payment has been collected. The fallback is AUDIBLE:
    log at ERROR level + write a ``smtp_fallback`` event to cortex claude_inbox
    so the operator is paged. Suppress the fallback with
    ``CONCERTO_TRANSACTIONAL_STRICT=1`` (raises + DLQ instead).

``critical=False`` — NON-CRITICAL (drip onboarding, marketing).
    Mailroom ONLY — no raw-SMTP escape hatch. Bypassing the pool risks burning
    warm-up reputation. On mailroom failure: DLQ + exception.

Env vars (loaded at service start from /etc/empire/env for concerto-backend
and /etc/concerto/env for concerto-drip-runner):
    MAILROOM_URL                 — mailroom HTTP base (default http://127.0.0.1:8079)
    CONCERTO_TRANSACTIONAL_STRICT — when "1", removes raw-SMTP fallback even for critical
    CONCERTO_SMTP_HOST, CONCERTO_SMTP_PORT, CONCERTO_SMTP_USER_NOREPLY,
    CONCERTO_SMTP_PASS_NOREPLY, CONCERTO_EMAIL_FROM, CONCERTO_EMAIL_REPLY_TO
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import smtplib
import sqlite3
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

try:
    from mailroom.client import MailroomClient, MailroomError
    _MAILROOM_AVAILABLE = True
except Exception:  # pragma: no cover — mailroom client SDK not installed
    MailroomClient = None  # type: ignore[assignment]
    MailroomError = Exception  # type: ignore[assignment,misc]
    _MAILROOM_AVAILABLE = False


_log = logging.getLogger(__name__)

_SUPPRESS_PATTERN = os.getenv("CONCERTO_SUPPRESS_EMAILS_TO", "").strip()
_SUPPRESS_RE = re.compile(_SUPPRESS_PATTERN, re.IGNORECASE) if _SUPPRESS_PATTERN else None

# Counter file for SMTP fallback occurrences — written alongside the DB.
_FALLBACK_COUNT_FILE = os.path.join(
    os.path.dirname(os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")),
    "smtp_fallback_count",
)


def _alert_mailroom_fallback(to: str, subject: str, reason: str) -> None:
    """Log at ERROR and write a smtp_fallback alert to cortex claude_inbox.

    Both are best-effort — must not propagate exceptions.
    """
    _log.error(
        "MAILROOM SMTP FALLBACK — transactional email bypassed mailroom pool: "
        "to=%s subject=%r reason=%s — check mailroom service health",
        to, subject, reason,
    )
    # Increment a file-based counter so ops dashboards can scrape it.
    try:
        current = 0
        try:
            current = int(open(_FALLBACK_COUNT_FILE).read().strip())
        except (FileNotFoundError, ValueError):
            pass
        with open(_FALLBACK_COUNT_FILE, "w") as fh:
            fh.write(str(current + 1))
    except Exception as exc:
        _log.warning("smtp_fallback counter write failed: %s", exc)
    # Write alert to cortex claude_inbox for operator visibility.
    try:
        payload = json.dumps({
            "severity": "warning",
            "to": to,
            "subject": subject,
            "reason": reason,
            "detail": "transactional email bypassed mailroom pool via raw-SMTP fallback",
        })
        conn = sqlite3.connect("/var/lib/cortex/cortex.db", timeout=3)
        conn.execute(
            "INSERT INTO claude_inbox(created_at,actor,project,kind,payload_json)"
            " VALUES(strftime('%s','now'),'concerto-transactional','concerto','smtp_fallback',?)",
            (payload,),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        _log.warning("cortex claude_inbox alert write failed: %s", exc)


class MigaduSMTPClient:
    def __init__(self):
        self.host = os.environ["CONCERTO_SMTP_HOST"]
        self.port = int(os.environ["CONCERTO_SMTP_PORT"])
        self.user = os.environ["CONCERTO_SMTP_USER_NOREPLY"]
        self.password = os.environ["CONCERTO_SMTP_PASS_NOREPLY"]
        self.from_addr = os.environ["CONCERTO_EMAIL_FROM"]
        self.reply_to = os.environ["CONCERTO_EMAIL_REPLY_TO"]
        # Explicit URL avoids mailroom.client DEFAULT_BASE_URL which defaults to
        # port 8099; the real mailroom service listens on 8079.
        mailroom_url = os.environ.get("MAILROOM_URL", "http://127.0.0.1:8079")
        self._mailroom: MailroomClient | None = (
            MailroomClient(base_url=mailroom_url) if _MAILROOM_AVAILABLE else None
        )

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: str | None = None,
        *,
        critical: bool = True,
        _bypass_suppress: bool = False,
    ) -> str:
        """Send email. Returns the Message-ID string.

        ``critical=True``  (default) — payment receipts, billing alerts.
            Mailroom primary; raw-SMTP fallback on unreachability (audible).
        ``critical=False`` — drip / onboarding / marketing.
            Mailroom only; DLQ + exception on failure, no raw-SMTP escape.

        Suppression returns the sentinel ``"<suppressed>"``.
        """
        # Defense-in-depth suppression — catches callers that bypass email_utils.
        if not _bypass_suppress and _SUPPRESS_RE and _SUPPRESS_RE.match(to.strip().lower()):
            print(f"[email-suppress] dropped email to {to} (subject={subject!r})", flush=True)
            return "<suppressed>"

        # 1. unified path — try mailroom first.
        if self._mailroom is not None:
            try:
                resp = self._mailroom.send(
                    to=to,
                    subject=subject,
                    body_html=html,
                    product="concerto",
                    send_kind="transactional",
                    brand="concerto",
                    idempotency_key=f"concerto:transactional:{to}:{subject}",
                )
            except MailroomError as exc:
                if not critical:
                    # Non-critical: no SMTP escape — preserve pool health.
                    self._write_dlq(to, subject, html, text,
                                    f"mailroom unreachable: {exc}", retries=0)
                    raise smtplib.SMTPException(
                        f"mailroom unreachable (non-critical, deferred to DLQ): {exc}"
                    )
                if os.getenv("CONCERTO_TRANSACTIONAL_STRICT") == "1":
                    self._write_dlq(to, subject, html, text,
                                    f"mailroom unreachable: {exc}", retries=0)
                    raise smtplib.SMTPException(
                        f"mailroom unreachable and STRICT mode: {exc}"
                    )
                # Critical + non-strict: audible fallback to raw SMTP.
                _alert_mailroom_fallback(to, subject, f"MailroomError: {exc}")
                # fall through to raw SMTP below
            else:
                status = resp.get("status")
                if status == "sent":
                    return (
                        resp.get("provider_message_id")
                        or resp.get("message_id")
                        or resp.get("tracking_id")
                        or "<mailroom>"
                    )
                if status == "suppressed":
                    return "<suppressed>"
                # status in ("blocked", "failed") — pool can't route this send.
                err = resp.get("error") or status
                if not critical:
                    # Non-critical: pool failure → DLQ, no SMTP bypass.
                    self._write_dlq(to, subject, html, text,
                                    f"mailroom {status}: {err}", retries=0)
                    raise smtplib.SMTPException(
                        f"mailroom {status}: {err} (non-critical, deferred to DLQ)"
                    )
                if os.getenv("CONCERTO_TRANSACTIONAL_STRICT") == "1":
                    self._write_dlq(to, subject, html, text,
                                    f"mailroom {status}: {err}", retries=0)
                    raise smtplib.SMTPException(f"mailroom {status}: {err}")
                # Critical + non-strict: audible fallback.
                _alert_mailroom_fallback(to, subject, f"mailroom {status}: {err}")
                # fall through to raw SMTP below
        else:
            # mailroom SDK not installed — should not happen in production.
            if not critical:
                self._write_dlq(to, subject, html, text,
                                "mailroom SDK not available", retries=0)
                raise smtplib.SMTPException(
                    "mailroom SDK not available (non-critical, deferred to DLQ)"
                )
            _log.error(
                "mailroom SDK not available — falling back to raw SMTP for critical send to %s", to
            )

        # 2. raw-SMTP fallback — only reached for critical sends.
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Concerto <{self.from_addr}>"
        msg["Reply-To"] = self.reply_to
        msg["To"] = to
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="concerto.run")

        if text:
            msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        last_exc: Exception | None = None
        for delay in (0, 1, 2, 4):
            if delay:
                time.sleep(delay)
            try:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(self.host, self.port, timeout=20) as s:
                    s.starttls(context=ctx)
                    s.login(self.user, self.password)
                    s.send_message(msg)
                return msg["Message-ID"]
            except smtplib.SMTPException as exc:
                last_exc = exc

        self._write_dlq(to, subject, html, text, str(last_exc), retries=3)
        raise last_exc  # type: ignore[misc]

    async def send_async(
        self,
        to: str,
        subject: str,
        html: str,
        text: str | None = None,
        *,
        critical: bool = True,
        _bypass_suppress: bool = False,
    ) -> str:
        """Async wrapper around send() — runs in a thread pool."""
        return await asyncio.to_thread(
            self.send, to, subject, html, text,
            critical=critical, _bypass_suppress=_bypass_suppress,
        )

    def _write_dlq(
        self,
        to: str,
        subject: str,
        html: str | None,
        text: str | None,
        error: str,
        retries: int,
    ) -> None:
        db_path = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path, timeout=5)
            conn.execute(
                "INSERT OR IGNORE INTO concerto_email_dead_letter"
                " (to_addr, subject, body_html, body_text, error, attempted_at, retries)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (to, subject, html, text, error, int(time.time()), retries),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # DLQ write must not propagate


_client: MigaduSMTPClient | None = None


def get_client() -> MigaduSMTPClient:
    """Return a process-level singleton MigaduSMTPClient."""
    global _client
    if _client is None:
        _client = MigaduSMTPClient()
    return _client
