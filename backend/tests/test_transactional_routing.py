"""Concerto's transactional client routes through mailroom first.

This pins OUTCOME 1 of the email-system goal for the concerto.run brand:
the noreply transactional path is no longer raw smtplib by default — it
goes through ``mailroom.client.send`` with brand="concerto",
send_kind="transactional", so warmup/quota/reputation/suppression all see
it. The raw-SMTP fallback only engages when mailroom itself is unreachable
(documented justified exception: transactional cannot block the purchase
flow if mailroom is down).

What is asserted here:
  * The default path calls ``MailroomClient.send`` with the right payload.
  * A "sent" response short-circuits — raw smtplib is NEVER touched.
  * A "suppressed" response returns the suppression sentinel.
  * On ``MailroomError`` (mailroom down), the raw SMTP fallback runs.
  * With ``CONCERTO_TRANSACTIONAL_STRICT=1``, a MailroomError raises
    instead of falling back.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


@pytest.fixture()
def env(monkeypatch):
    """Wire required env vars and reload the transactional module fresh.

    Each test gets an isolated MigaduSMTPClient with a stub MailroomClient
    attached so we can intercept calls without touching the network.
    """
    monkeypatch.setenv("CONCERTO_SMTP_HOST", "smtp.test")
    monkeypatch.setenv("CONCERTO_SMTP_PORT", "587")
    monkeypatch.setenv("CONCERTO_SMTP_USER_NOREPLY", "noreply@concerto.run")
    monkeypatch.setenv("CONCERTO_SMTP_PASS_NOREPLY", "test-pw")
    monkeypatch.setenv("CONCERTO_EMAIL_FROM", "noreply@concerto.run")
    monkeypatch.setenv("CONCERTO_EMAIL_REPLY_TO", "ops@concerto.run")
    monkeypatch.delenv("CONCERTO_TRANSACTIONAL_STRICT", raising=False)
    monkeypatch.delenv("CONCERTO_SUPPRESS_EMAILS_TO", raising=False)

    # Reload so the module-level regex picks up the env state.
    if "concerto.transactional" in sys.modules:
        del sys.modules["concerto.transactional"]
    import concerto.transactional as tx
    importlib.reload(tx)
    return tx


class _StubMailroom:
    """Records every call to .send(); returns a configurable response."""

    def __init__(self, response):
        self.response = response
        self.calls: list[dict] = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _boom_smtp(*_a, **_kw):
    raise AssertionError("raw SMTP must not be called when mailroom succeeds")


def test_default_path_goes_through_mailroom(env, monkeypatch):
    """A successful mailroom send returns the provider id and never touches smtplib."""
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", _boom_smtp)

    client = env.MigaduSMTPClient()
    stub = _StubMailroom({
        "status": "sent",
        "tracking_id": "mr_test_001",
        "provider_message_id": "pmid-concerto-001",
        "inbox_id": 1,
    })
    client._mailroom = stub

    msg_id = client.send(
        "buyer@example.com", "Welcome to Concerto",
        "<p>hi</p>", text="hi",
    )

    assert msg_id == "pmid-concerto-001"
    assert len(stub.calls) == 1
    call = stub.calls[0]
    assert call["to"] == "buyer@example.com"
    assert call["subject"] == "Welcome to Concerto"
    assert call["brand"] == "concerto"
    assert call["send_kind"] == "transactional"
    assert call["product"] == "concerto"
    assert call["idempotency_key"].startswith("concerto:transactional:")


def test_mailroom_suppressed_returns_sentinel(env, monkeypatch):
    """Suppression must not fall back to raw SMTP — sealed means sealed."""
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", _boom_smtp)

    client = env.MigaduSMTPClient()
    client._mailroom = _StubMailroom({
        "status": "suppressed",
        "tracking_id": "mr_test_002",
        "error": "recipient suppressed",
    })

    out = client.send("blocked@example.com", "Receipt", "<p>x</p>")
    assert out == "<suppressed>"


def test_mailroom_unreachable_falls_back_to_smtp(env, monkeypatch):
    """When mailroom is down, transactional MUST still ship via raw SMTP.

    Transactional cannot block the purchase flow — this is the documented,
    bounded exception for concerto.
    """
    captured: dict = {}

    class _StubSMTP:
        def __init__(self, host, port, timeout=20):
            captured["host"] = host
            captured["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context=None):
            captured["starttls"] = True

        def login(self, user, password):
            captured["user"] = user

        def send_message(self, msg):
            captured["to"] = msg["To"]
            captured["subject"] = msg["Subject"]

    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", _StubSMTP)

    client = env.MigaduSMTPClient()
    client._mailroom = _StubMailroom(env.MailroomError("connection refused"))

    msg_id = client.send("buyer@example.com", "Order Receipt", "<p>thanks</p>")

    # The raw-SMTP path stamps a Message-ID derived from concerto.run.
    assert "@concerto.run" in msg_id
    assert captured["host"] == "smtp.test"
    assert captured["to"] == "buyer@example.com"
    assert captured["subject"] == "Order Receipt"
    assert captured["user"] == "noreply@concerto.run"


def test_strict_mode_raises_when_mailroom_down(env, monkeypatch):
    """STRICT mode disables the fallback — outage → smtplib.SMTPException + DLQ."""
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", _boom_smtp)
    monkeypatch.setenv("CONCERTO_TRANSACTIONAL_STRICT", "1")

    dlq_writes: list[dict] = []

    client = env.MigaduSMTPClient()
    client._mailroom = _StubMailroom(env.MailroomError("connection refused"))
    monkeypatch.setattr(
        client, "_write_dlq",
        lambda to, subject, html, text, error, retries: dlq_writes.append(
            {"to": to, "error": error, "retries": retries}
        ),
    )

    with pytest.raises(smtplib.SMTPException) as ei:
        client.send("buyer@example.com", "Order Receipt", "<p>thanks</p>")
    assert "mailroom unreachable" in str(ei.value)
    assert len(dlq_writes) == 1
    assert dlq_writes[0]["to"] == "buyer@example.com"


def test_mailroom_failed_falls_back_in_non_strict(env, monkeypatch):
    """A mailroom-side ``failed`` (no inbox available) falls back to raw SMTP.

    This protects transactional sends from a misconfigured pool — receipt
    still ships, operator notices via the digest. STRICT mode would honour
    the failure instead.
    """
    captured: dict = {}

    class _StubSMTP:
        def __init__(self, host, port, timeout=20): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, context=None): captured["starttls"] = True
        def login(self, user, password): captured["user"] = user
        def send_message(self, msg): captured["sent"] = True

    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", _StubSMTP)

    client = env.MigaduSMTPClient()
    client._mailroom = _StubMailroom({
        "status": "failed",
        "tracking_id": "mr_test_003",
        "error": "no inbox available",
        "inbox_id": None,
    })

    msg_id = client.send("buyer@example.com", "Receipt", "<p>x</p>")
    assert "@concerto.run" in msg_id
    assert captured.get("sent") is True


def test_suppression_pattern_short_circuits_before_mailroom(env, monkeypatch):
    """The CONCERTO_SUPPRESS_EMAILS_TO defense-in-depth filter still runs first."""
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", _boom_smtp)
    monkeypatch.setenv("CONCERTO_SUPPRESS_EMAILS_TO", r"^smoke@.*")

    # Reload to pick up the regex.
    import concerto.transactional as tx
    importlib.reload(tx)

    stub = _StubMailroom({
        "status": "sent",
        "tracking_id": "x",
        "provider_message_id": "y",
        "inbox_id": 1,
    })
    client = tx.MigaduSMTPClient()
    client._mailroom = stub

    out = client.send("smoke@example.com", "subject", "<p>x</p>")
    assert out == "<suppressed>"
    assert stub.calls == []  # never reached mailroom

    # Reset module to keep test isolation for any later tests in the file.
    monkeypatch.delenv("CONCERTO_SUPPRESS_EMAILS_TO", raising=False)
    importlib.reload(tx)
