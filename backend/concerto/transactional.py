"""Concerto transactional email client — routes through mailroom, falls back
to raw Migadu SMTP if mailroom is unreachable.

Primary path: ``mailroom.client.send`` with ``send_kind="transactional"`` and
``brand="concerto"``. mailroom owns the inbox pool, warmup, rotation, and
reputation/suppression — this is the unified-path rule (see
/opt/mailroom/docs/EMAIL_SENDERS_INVENTORY.md, row #4).

Fallback path: raw ``smtplib`` over STARTTLS:587 to Migadu. Transactional
sends (receipts, billing alerts) must not block the purchase flow if
mailroom is offline — the inventory documents this as a bounded, justified
exception. Disable the fallback by setting ``CONCERTO_TRANSACTIONAL_STRICT=1``
(treats a mailroom outage as a hard send failure → DLQ).

Env vars (loaded from /etc/cortex/env at service start):
    MAILROOM_URL                 — mailroom HTTP endpoint (default 127.0.0.1:8099)
    CONCERTO_TRANSACTIONAL_STRICT — when "1", drop the raw-SMTP fallback
    CONCERTO_SMTP_HOST, CONCERTO_SMTP_PORT, CONCERTO_SMTP_USER_NOREPLY,
    CONCERTO_SMTP_PASS_NOREPLY, CONCERTO_EMAIL_FROM, CONCERTO_EMAIL_REPLY_TO
"""

from __future__ import annotations

import asyncio
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


class MigaduSMTPClient:
    def __init__(self):
        self.host = os.environ["CONCERTO_SMTP_HOST"]
        self.port = int(os.environ["CONCERTO_SMTP_PORT"])
        self.user = os.environ["CONCERTO_SMTP_USER_NOREPLY"]
        self.password = os.environ["CONCERTO_SMTP_PASS_NOREPLY"]
        self.from_addr = os.environ["CONCERTO_EMAIL_FROM"]
        self.reply_to = os.environ["CONCERTO_EMAIL_REPLY_TO"]
        self._mailroom: MailroomClient | None = (
            MailroomClient() if _MAILROOM_AVAILABLE else None
        )

    def send(self, to: str, subject: str, html: str, text: str | None = None, *, _bypass_suppress: bool = False) -> str:
        """Send email synchronously. Returns the Message-ID string.

        Order of attempts:
          1. Route through mailroom (unified path, brand="concerto",
             send_kind="transactional"). Honours suppression + warmup.
          2. If mailroom is unreachable (MailroomError) AND
             ``CONCERTO_TRANSACTIONAL_STRICT`` is not set, fall back to raw
             Migadu SMTP — receipts must still ship if the pool service died.

        Raises smtplib.SMTPException only if every path failed and DLQ was
        written. Suppression returns the sentinel ``"<suppressed>"``.
        """
        # Defense-in-depth: respect CONCERTO_SUPPRESS_EMAILS_TO at the SMTP
        # layer. send_email() in email_utils.py also enforces this, but any
        # call site that directly uses get_client().send(...) (e.g. drip_runner,
        # trial_reaper) would otherwise bypass the filter and spam the operator.
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
                if os.getenv("CONCERTO_TRANSACTIONAL_STRICT") == "1":
                    self._write_dlq(to, subject, html, text,
                                    f"mailroom unreachable: {exc}", retries=0)
                    raise smtplib.SMTPException(
                        f"mailroom unreachable and STRICT mode: {exc}"
                    )
                _log.warning("mailroom unreachable, falling back to raw SMTP: %s", exc)
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
                # status in ("blocked", "failed") — pool can't route this send
                # right now. For transactional we treat that as "mailroom can't
                # do it, fall back to raw SMTP" so the customer still gets
                # their receipt. In STRICT mode we honour mailroom's verdict.
                if os.getenv("CONCERTO_TRANSACTIONAL_STRICT") == "1":
                    err = resp.get("error") or status
                    self._write_dlq(to, subject, html, text,
                                    f"mailroom {status}: {err}", retries=0)
                    raise smtplib.SMTPException(f"mailroom {status}: {err}")
                _log.warning(
                    "mailroom returned %s (%s), falling back to raw SMTP",
                    status, resp.get("error"),
                )

        # 2. fallback path — raw Migadu SMTP (today's behaviour).
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

    async def send_async(self, to: str, subject: str, html: str, text: str | None = None, *, _bypass_suppress: bool = False) -> str:
        """Async wrapper around send() — runs in a thread pool."""
        return await asyncio.to_thread(self.send, to, subject, html, text, _bypass_suppress=_bypass_suppress)

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
