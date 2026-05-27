"""Concerto transactional email client — Migadu SMTP over STARTTLS:587.

Env vars required (loaded from /etc/empire/env at service start):
    CONCERTO_SMTP_HOST, CONCERTO_SMTP_PORT, CONCERTO_SMTP_USER_NOREPLY,
    CONCERTO_SMTP_PASS_NOREPLY, CONCERTO_EMAIL_FROM, CONCERTO_EMAIL_REPLY_TO

All mail to concerto.run recipients goes through this module.
Resend (RESEND_API_KEY) is kept only for strandedgrid.com outbound.
"""

from __future__ import annotations

import asyncio
import os
import smtplib
import sqlite3
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid


class MigaduSMTPClient:
    def __init__(self):
        self.host = os.environ["CONCERTO_SMTP_HOST"]
        self.port = int(os.environ["CONCERTO_SMTP_PORT"])
        self.user = os.environ["CONCERTO_SMTP_USER_NOREPLY"]
        self.password = os.environ["CONCERTO_SMTP_PASS_NOREPLY"]
        self.from_addr = os.environ["CONCERTO_EMAIL_FROM"]
        self.reply_to = os.environ["CONCERTO_EMAIL_REPLY_TO"]

    def send(self, to: str, subject: str, html: str, text: str | None = None) -> str:
        """Send email synchronously. Retries 3× (1s/2s/4s backoff). Writes DLQ on failure.

        Returns the Message-ID string.
        Raises smtplib.SMTPException if all retries exhausted (after DLQ write).
        """
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

    async def send_async(self, to: str, subject: str, html: str, text: str | None = None) -> str:
        """Async wrapper around send() — runs in a thread pool."""
        return await asyncio.to_thread(self.send, to, subject, html, text)

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
