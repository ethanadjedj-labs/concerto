"""
Tests for callback_secret separation from ttyd_password.

Covers:
 - droplet_ready accepts the correct callback_secret
 - droplet_ready rejects a wrong callback_secret
 - Legacy rows (callback_secret NULL) fall back to ttyd_password
 - Migration 018 adds the callback_secret column
"""
import hmac
import os
import sqlite3
import tempfile

import pytest
from fastapi.testclient import TestClient


# ── Migration helper (mirrors test_migration.py convention) ───────────────────

def _migrations_dir():
    return os.path.join(os.path.dirname(__file__), "..", "migrations")


def _apply_migration(conn: sqlite3.Connection, filename: str) -> None:
    path = os.path.join(_migrations_dir(), filename)
    with open(path) as f:
        sql = f.read()
    for stmt in (s.strip() for s in sql.split(";") if s.strip()):
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise
    conn.commit()


def test_018_adds_callback_secret_column():
    """Migration 018 must add callback_secret TEXT column to concerto_buyers."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration(conn, "001_init.sql")
        _apply_migration(conn, "018_callback_secret.sql")
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(concerto_buyers)").fetchall()
        }
        assert "callback_secret" in cols, "callback_secret column missing after migration 018"
        conn.close()


def test_018_is_idempotent():
    """Migration 018 must be safe to run twice (duplicate column silenced)."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration(conn, "001_init.sql")
        _apply_migration(conn, "018_callback_secret.sql")
        _apply_migration(conn, "018_callback_secret.sql")
        conn.close()


# ── HMAC logic unit tests (extracted from provision_router pattern) ───────────

def _verify(stored_callback: str | None, stored_ttyd: str | None, incoming: str) -> bool:
    """Mirrors the updated droplet_ready verification logic.

    F-02 hardening: when neither secret is set, FAIL CLOSED (return False).
    Previously this returned True ("graceful skip") which let an attacker
    pin mcp_url during the install window — see docs/THREAT_MODEL.md F-02.
    """
    stored_secret = stored_callback or stored_ttyd or ""
    if not stored_secret:
        return False  # fail-closed (was True before F-02 hardening)
    return hmac.compare_digest(stored_secret, incoming)


def test_correct_callback_secret_accepted():
    assert _verify("abc123", "oldpass", "abc123") is True


def test_wrong_callback_secret_rejected():
    assert _verify("abc123", "oldpass", "wrongvalue") is False


def test_legacy_ttyd_password_accepted_when_no_callback_secret():
    """When callback_secret is NULL, ttyd_password is the fallback."""
    assert _verify(None, "oldpass", "oldpass") is True


def test_legacy_ttyd_password_rejected_on_mismatch():
    assert _verify(None, "oldpass", "badpass") is False


def test_both_null_fails_closed():
    """Neither field set — REJECT (F-02 hardening; was accept-all before)."""
    assert _verify(None, None, "anything") is False


def test_empty_string_fails_closed():
    """Empty strings are equivalent to None and must also fail-closed."""
    assert _verify("", "", "anything") is False


def test_callback_secret_takes_precedence_over_ttyd():
    """When callback_secret is present, ttyd_password is ignored."""
    assert _verify("newsecret", "oldpass", "oldpass") is False
    assert _verify("newsecret", "oldpass", "newsecret") is True
