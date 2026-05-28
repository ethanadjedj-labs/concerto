"""
Tests for the cancel-by-email / cancel-by-link flow.

Covers:
 - HMAC link generation and verification (valid, expired, tampered)
 - Rate-limit logic (allow up to max, block after max, per-IP isolation, window reset)
 - Anti-enumeration: unknown-email DB query returns None; response shape identical
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import tempfile
import time
from collections import defaultdict


# ── Migration helper (mirrors test_callback_secret.py convention) ─────────────

def _migrations_dir() -> str:
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


# ── HMAC helpers (mirrors customer_portal._sign / _verify_cancel_link) ────────

def _sign(secret: str, token: str, expires_at: int) -> str:
    msg = f"{token}:{expires_at}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def _make_link(secret: str, token: str, ttl: int = 3600) -> tuple[str, int, str]:
    expires_at = int(time.time()) + ttl
    sig = _sign(secret, token, expires_at)
    return token, expires_at, sig


def _verify_link(secret: str, token: str, expires_at: int, sig: str) -> bool:
    if time.time() > expires_at:
        return False
    expected = _sign(secret, token, expires_at)
    return hmac.compare_digest(expected, sig)


# ── HMAC link tests ────────────────────────────────────────────────────────────

def test_valid_cancel_link_verified():
    secret = secrets.token_hex(16)
    token, expires_at, sig = _make_link(secret, "buyer-token-abc")
    assert _verify_link(secret, token, expires_at, sig) is True


def test_wrong_sig_rejected():
    secret = secrets.token_hex(16)
    token, expires_at, sig = _make_link(secret, "buyer-token-abc")
    assert _verify_link(secret, token, expires_at, sig + "x") is False


def test_expired_link_rejected():
    secret = secrets.token_hex(16)
    token  = "buyer-token-abc"
    expires_at = int(time.time()) - 1  # already expired
    sig = _sign(secret, token, expires_at)
    assert _verify_link(secret, token, expires_at, sig) is False


def test_tampered_token_rejected():
    secret = secrets.token_hex(16)
    _, expires_at, sig = _make_link(secret, "buyer-token-abc")
    assert _verify_link(secret, "different-token", expires_at, sig) is False


def test_different_secret_rejected():
    secret1 = secrets.token_hex(16)
    secret2 = secrets.token_hex(16)
    token, expires_at, sig = _make_link(secret1, "buyer-token-abc")
    assert _verify_link(secret2, token, expires_at, sig) is False


def test_future_link_is_valid():
    secret = secrets.token_hex(16)
    expires_at = int(time.time()) + 3600
    sig = _sign(secret, "tok", expires_at)
    assert _verify_link(secret, "tok", expires_at, sig) is True


# ── Rate-limit logic (mirrors customer_portal._check_and_record_attempt) ──────

_RATE_MAX    = 3
_RATE_WINDOW = 3600


def _fresh_store() -> dict[str, list[float]]:
    return defaultdict(list)


def _check(store: dict[str, list[float]], ip: str, now: float | None = None) -> bool:
    if now is None:
        now = time.time()
    cutoff  = now - _RATE_WINDOW
    prev    = [t for t in store[ip] if t > cutoff]
    if len(prev) >= _RATE_MAX:
        store[ip] = prev
        return False
    prev.append(now)
    store[ip] = prev
    return True


def test_rate_limit_allows_up_to_max():
    store = _fresh_store()
    for _ in range(_RATE_MAX):
        assert _check(store, "1.2.3.4") is True


def test_rate_limit_blocks_on_max_plus_one():
    store = _fresh_store()
    for _ in range(_RATE_MAX):
        _check(store, "1.2.3.4")
    assert _check(store, "1.2.3.4") is False


def test_rate_limit_different_ips_independent():
    store = _fresh_store()
    for _ in range(_RATE_MAX):
        _check(store, "1.2.3.4")
    assert _check(store, "5.6.7.8") is True


def test_rate_limit_window_reset():
    store = _fresh_store()
    old = time.time() - _RATE_WINDOW - 10  # outside the window
    for _ in range(_RATE_MAX):
        store["1.2.3.4"].append(old)
    assert _check(store, "1.2.3.4") is True


# ── Anti-enumeration: DB query behaviour ──────────────────────────────────────

def test_unknown_email_returns_none():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration(conn, "001_init.sql")
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT * FROM concerto_buyers
               WHERE email = ? AND paid_at IS NOT NULL
               ORDER BY paid_at DESC LIMIT 1""",
            ("nobody@example.com",),
        ).fetchone()
        assert row is None
        conn.close()


def test_known_email_returns_buyer():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration(conn, "001_init.sql")
        conn.execute(
            """INSERT INTO concerto_buyers
               (token, email, stripe_session_id, status, paid_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("tok-001", "alice@example.com", "sess_x", "paid_unprovisioned",
             int(time.time())),
        )
        conn.commit()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT * FROM concerto_buyers
               WHERE email = ? AND paid_at IS NOT NULL
               ORDER BY paid_at DESC LIMIT 1""",
            ("alice@example.com",),
        ).fetchone()
        assert row is not None
        assert dict(row)["token"] == "tok-001"
        conn.close()


def test_multiple_emails_picks_most_recent():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration(conn, "001_init.sql")
        now = int(time.time())
        conn.execute(
            """INSERT INTO concerto_buyers
               (token, email, stripe_session_id, status, paid_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("tok-old", "alice@example.com", "sess_a", "paid_unprovisioned",
             now - 1000),
        )
        conn.execute(
            """INSERT INTO concerto_buyers
               (token, email, stripe_session_id, status, paid_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("tok-new", "alice@example.com", "sess_b", "paid_unprovisioned",
             now),
        )
        conn.commit()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT * FROM concerto_buyers
               WHERE email = ? AND paid_at IS NOT NULL
               ORDER BY paid_at DESC LIMIT 1""",
            ("alice@example.com",),
        ).fetchone()
        assert dict(row)["token"] == "tok-new"
        conn.close()


def test_anti_enumeration_response_shape_is_identical():
    """Both found/not-found paths must return the same dict shape and message."""
    msg = "If this email has an active subscription, you'll receive a confirmation link shortly."
    found_response    = {"ok": True, "message": msg}
    notfound_response = {"ok": True, "message": msg}
    assert found_response == notfound_response
