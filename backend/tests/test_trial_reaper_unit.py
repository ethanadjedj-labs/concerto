"""Unit tests for concerto.trial_reaper.

Covers:
  - _trial_duration_label: pure function
  - _find_expired_trials / _find_pre_expiry_warnings: DB queries
  - _mark_expired / _mark_pre_warned: DB writes
  - _reap_once: orchestration (all IO mocked)
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import time
from unittest.mock import AsyncMock, patch

_SCHEMA = """
    CREATE TABLE concerto_buyers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        email TEXT,
        provider TEXT DEFAULT 'digitalocean',
        vps_id TEXT, vps_ip TEXT, cf_tunnel_id TEXT,
        mcp_url TEXT, bearer_token TEXT, ssh_keypair_private_path TEXT,
        status TEXT DEFAULT 'active',
        paid_at INTEGER, provisioned_at INTEGER, installed_at INTEGER,
        plan TEXT DEFAULT 'trial',
        ttyd_public_url TEXT, runtime_state TEXT,
        expires_at INTEGER, github_token TEXT, pre_expiry_warned_at INTEGER,
        failure_reason TEXT
    )
"""


def _make_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _insert(conn: sqlite3.Connection, **kw) -> None:
    now = int(time.time())
    defaults = dict(
        token="tok-001", email="t@example.com", plan="trial", status="active",
        vps_id="d-111", vps_ip="1.2.3.4", cf_tunnel_id="cf-001",
        paid_at=now - 86400, expires_at=now - 3600,
        pre_expiry_warned_at=None, github_token=None,
    )
    defaults.update(kw)
    cols = ", ".join(defaults)
    ph = ", ".join("?" * len(defaults))
    conn.execute(f"INSERT INTO concerto_buyers ({cols}) VALUES ({ph})", list(defaults.values()))
    conn.commit()


# ── _trial_duration_label ─────────────────────────────────────────────────────

class TestTrialDurationLabel:
    def _label(self, expires_at: int, paid_at: int) -> str:
        from concerto.trial_reaper import _trial_duration_label
        return _trial_duration_label(expires_at, paid_at)

    def test_30min_label(self):
        assert self._label(1800, 0) == "30-minute"

    def test_48h_label(self):
        assert self._label(48 * 3600, 0) == "48-hour"

    def test_intermediate_rounds_to_hours(self):
        label = self._label(4 * 3600, 0)
        assert "4" in label and "hour" in label

    def test_negative_diff_clamps_to_30min(self):
        # expires_at < paid_at → max(0, negative) → 0 s → "30-minute"
        assert self._label(100, 200) == "30-minute"


# ── _find_expired_trials ──────────────────────────────────────────────────────

class TestFindExpiredTrials:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def _run(self):
        import concerto.trial_reaper as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            return m._find_expired_trials()
        finally:
            m.DB_PATH = orig

    def test_past_expiry_active_trial_found(self):
        _insert(self.conn)
        result = self._run()
        assert len(result) == 1
        assert result[0]["token"] == "tok-001"

    def test_future_expiry_excluded(self):
        _insert(self.conn, expires_at=int(time.time()) + 3600)
        assert self._run() == []

    def test_already_expired_status_excluded(self):
        _insert(self.conn, status="trial_expired")
        assert self._run() == []

    def test_trial_upgraded_excluded(self):
        _insert(self.conn, status="trial_upgraded")
        assert self._run() == []

    def test_non_trial_plan_excluded(self):
        _insert(self.conn, plan="solo")
        assert self._run() == []

    def test_result_contains_expected_fields(self):
        _insert(self.conn)
        row = self._run()[0]
        for field in ("token", "email", "vps_id", "cf_tunnel_id"):
            assert field in row


# ── _find_pre_expiry_warnings ─────────────────────────────────────────────────

class TestFindPreExpiryWarnings:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def _run(self):
        import concerto.trial_reaper as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            return m._find_pre_expiry_warnings()
        finally:
            m.DB_PATH = orig

    def test_long_trial_near_expiry_selected(self):
        now = int(time.time())
        paid = now - (47 * 3600)
        expires = paid + 48 * 3600  # ~1 h left, well within 2h10 window
        _insert(self.conn, plan="trial", status="active",
                paid_at=paid, expires_at=expires, pre_expiry_warned_at=None)
        assert len(self._run()) == 1

    def test_already_warned_excluded(self):
        now = int(time.time())
        paid = now - (47 * 3600)
        expires = paid + 48 * 3600
        _insert(self.conn, plan="trial", status="active",
                paid_at=paid, expires_at=expires, pre_expiry_warned_at=now - 100)
        assert self._run() == []

    def test_short_30min_trial_excluded(self):
        now = int(time.time())
        paid = now - 1500
        expires = paid + 1800  # 30-min trial
        _insert(self.conn, plan="trial", status="active",
                paid_at=paid, expires_at=expires, pre_expiry_warned_at=None)
        assert self._run() == []

    def test_already_expired_excluded(self):
        now = int(time.time())
        _insert(self.conn, plan="trial", status="active",
                paid_at=now - 48 * 3600, expires_at=now - 60,
                pre_expiry_warned_at=None)
        assert self._run() == []


# ── _mark_expired / _mark_pre_warned ─────────────────────────────────────────

class TestMarkFunctions:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)
        _insert(self.conn, token="mark-tok", status="active", pre_expiry_warned_at=None)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def test_mark_expired_sets_status(self):
        import concerto.trial_reaper as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            m._mark_expired("mark-tok")
        finally:
            m.DB_PATH = orig
        row = self.conn.execute(
            "SELECT status FROM concerto_buyers WHERE token='mark-tok'"
        ).fetchone()
        assert row[0] == "trial_expired"

    def test_mark_pre_warned_writes_timestamp(self):
        import concerto.trial_reaper as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        before = int(time.time())
        try:
            m._mark_pre_warned("mark-tok")
        finally:
            m.DB_PATH = orig
        row = self.conn.execute(
            "SELECT pre_expiry_warned_at FROM concerto_buyers WHERE token='mark-tok'"
        ).fetchone()
        assert row[0] is not None and row[0] >= before


# ── _reap_once orchestration ──────────────────────────────────────────────────

class TestReapOnce:
    def _buyer(self, **kw):
        now = int(time.time())
        b = dict(token="b-tok", email="b@example.com", vps_id="d-1",
                 cf_tunnel_id="cf-1", expires_at=now - 100, paid_at=now - 3700)
        b.update(kw)
        return b

    def test_no_expired_no_warn_returns_zero(self):
        import concerto.trial_reaper as m
        with (
            patch.object(m, "_find_expired_trials", return_value=[]),
            patch.object(m, "_find_pre_expiry_warnings", return_value=[]),
        ):
            assert asyncio.run(m._reap_once()) == 0

    def test_one_expired_marks_destroys_emails(self):
        import concerto.trial_reaper as m
        marked, destroyed, emailed = [], [], []
        with (
            patch.object(m, "_find_expired_trials", return_value=[self._buyer()]),
            patch.object(m, "_find_pre_expiry_warnings", return_value=[]),
            patch.object(m, "_mark_expired", side_effect=lambda t: marked.append(t)),
            patch.object(m, "_destroy_droplet",
                         new=AsyncMock(side_effect=lambda d, c: destroyed.append(d))),
            patch.object(m, "_send_expired_email",
                         new=AsyncMock(side_effect=lambda e, *a, **k: emailed.append(e))),
            patch.object(m, "_send_pre_expiry_email", new=AsyncMock()),
        ):
            count = asyncio.run(m._reap_once())
        assert count == 1
        assert "b-tok" in marked
        assert "d-1" in destroyed
        assert "b@example.com" in emailed

    def test_mark_expired_called_before_destroy(self):
        import concerto.trial_reaper as m
        order = []
        with (
            patch.object(m, "_find_expired_trials", return_value=[self._buyer()]),
            patch.object(m, "_find_pre_expiry_warnings", return_value=[]),
            patch.object(m, "_mark_expired", side_effect=lambda t: order.append("mark")),
            patch.object(m, "_destroy_droplet",
                         new=AsyncMock(side_effect=lambda *a: order.append("destroy"))),
            patch.object(m, "_send_expired_email", new=AsyncMock()),
            patch.object(m, "_send_pre_expiry_email", new=AsyncMock()),
        ):
            asyncio.run(m._reap_once())
        assert order[0] == "mark"

    def test_pre_expiry_warns_marked_and_emailed(self):
        import concerto.trial_reaper as m
        warned, emailed = [], []
        warn = [{"token": "w-tok", "email": "w@example.com"}]
        with (
            patch.object(m, "_find_expired_trials", return_value=[]),
            patch.object(m, "_find_pre_expiry_warnings", return_value=warn),
            patch.object(m, "_mark_pre_warned", side_effect=lambda t: warned.append(t)),
            patch.object(m, "_send_pre_expiry_email",
                         new=AsyncMock(side_effect=lambda e, t: emailed.append(e))),
        ):
            count = asyncio.run(m._reap_once())
        assert count == 1
        assert "w-tok" in warned
        assert "w@example.com" in emailed

    def test_multiple_expired_all_reaped(self):
        import concerto.trial_reaper as m
        buyers = [self._buyer(token=f"tok-{i}", vps_id=f"d-{i}") for i in range(3)]
        with (
            patch.object(m, "_find_expired_trials", return_value=buyers),
            patch.object(m, "_find_pre_expiry_warnings", return_value=[]),
            patch.object(m, "_mark_expired"),
            patch.object(m, "_destroy_droplet", new=AsyncMock()),
            patch.object(m, "_send_expired_email", new=AsyncMock()),
            patch.object(m, "_send_pre_expiry_email", new=AsyncMock()),
        ):
            count = asyncio.run(m._reap_once())
        assert count == 3

    def test_empty_email_passed_through_to_sender(self):
        import concerto.trial_reaper as m
        emailed = []
        buyer = self._buyer(email="")
        with (
            patch.object(m, "_find_expired_trials", return_value=[buyer]),
            patch.object(m, "_find_pre_expiry_warnings", return_value=[]),
            patch.object(m, "_mark_expired"),
            patch.object(m, "_destroy_droplet", new=AsyncMock()),
            patch.object(m, "_send_expired_email",
                         new=AsyncMock(side_effect=lambda e, *a, **k: emailed.append(e))),
            patch.object(m, "_send_pre_expiry_email", new=AsyncMock()),
        ):
            asyncio.run(m._reap_once())
        assert emailed == [""]
