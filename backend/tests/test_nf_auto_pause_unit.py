"""Unit tests for concerto.nf_auto_pause — paths NOT covered by test_auto_pause_resume.py.

test_auto_pause_resume.py already covers:
  - _get_eligible_buyers (status filtering, null last_active, provider, vps_id)
  - run_pause_pass dry_run mode

This file covers:
  - _set_runtime_paused: DB write
  - run_pause_pass (non-dry-run): suspend called, DB updated, log_lifecycle_event called
  - run_pause_pass error path: suspend raises → error recorded, paused count not incremented
  - run_pause_pass no eligible buyers: zero paused
"""
from __future__ import annotations

import asyncio
import importlib
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
        provider TEXT DEFAULT 'northflank',
        vps_id TEXT, vps_ip TEXT,
        mcp_url TEXT, bearer_token TEXT,
        status TEXT DEFAULT 'active',
        paid_at INTEGER, plan TEXT DEFAULT 'solo',
        ttyd_public_url TEXT, runtime_state TEXT,
        last_active_at INTEGER
    )
"""


def _make_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _insert(conn: sqlite3.Connection, **kw) -> None:
    defaults = dict(
        token="nf-tok-001", email="nf@example.com",
        provider="northflank", vps_id="svc-nf1",
        status="active", plan="solo",
        last_active_at=int(time.time()) - 3600,
        runtime_state=None,
    )
    defaults.update(kw)
    cols = ", ".join(defaults)
    ph = ", ".join("?" * len(defaults))
    conn.execute(f"INSERT INTO concerto_buyers ({cols}) VALUES ({ph})", list(defaults.values()))
    conn.commit()


# ── _set_runtime_paused ───────────────────────────────────────────────────────

class TestSetRuntimePaused:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)
        _insert(self.conn, token="set-rt-tok", runtime_state=None)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def test_sets_runtime_state_paused(self):
        import concerto.nf_auto_pause as m
        orig, m._DB_PATH = m._DB_PATH, self.path
        try:
            m._set_runtime_paused("set-rt-tok", int(time.time()))
        finally:
            m._DB_PATH = orig
        row = self.conn.execute(
            "SELECT runtime_state FROM concerto_buyers WHERE token='set-rt-tok'"
        ).fetchone()
        assert row[0] == "paused"

    def test_unknown_token_no_exception(self):
        import concerto.nf_auto_pause as m
        orig, m._DB_PATH = m._DB_PATH, self.path
        try:
            m._set_runtime_paused("ghost", int(time.time()))
        finally:
            m._DB_PATH = orig


# ── run_pause_pass (non-dry-run) ──────────────────────────────────────────────

class TestRunPausePassActual:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def _run(self, buyers, suspend_side_effect=None):
        import concerto.nf_auto_pause as m
        orig_db, m._DB_PATH = m._DB_PATH, self.path
        orig_dry, m._DRY_RUN = m._DRY_RUN, False

        suspend_mock = AsyncMock(side_effect=suspend_side_effect)
        log_mock = AsyncMock()

        try:
            with (
                patch.object(m, "_get_eligible_buyers", return_value=buyers),
                patch("concerto.provider_factory.suspend", suspend_mock),
                patch("concerto.db.log_lifecycle_event", log_mock),
                patch.object(m, "_set_runtime_paused"),
            ):
                return asyncio.run(m.run_pause_pass()), suspend_mock, log_mock
        finally:
            m._DB_PATH = orig_db
            m._DRY_RUN = orig_dry

    def test_no_eligible_zero_paused(self):
        result, _, _ = self._run([])
        assert result["paused"] == 0
        assert result["eligible"] == 0

    def test_one_eligible_suspend_called(self):
        buyers = [dict(token="b1", vps_id="svc-1", email="a@b.com",
                       last_active_at=int(time.time()) - 3600)]
        result, suspend_mock, _ = self._run(buyers)
        assert result["paused"] == 1
        assert result["errors"] == []
        suspend_mock.assert_called_once()
        _, kwargs = suspend_mock.call_args
        assert kwargs["vps_id"] == "svc-1"

    def test_suspend_failure_recorded_in_errors(self):
        buyers = [dict(token="b2", vps_id="svc-2", email="x@y.com",
                       last_active_at=int(time.time()) - 3600)]
        result, _, _ = self._run(buyers, suspend_side_effect=Exception("NF 503"))
        assert result["paused"] == 0
        assert len(result["errors"]) == 1
        assert "pause_failed" in result["errors"][0]

    def test_log_lifecycle_event_called_on_success(self):
        buyers = [dict(token="b3", vps_id="svc-3", email="z@z.com",
                       last_active_at=int(time.time()) - 3600)]
        _, _, log_mock = self._run(buyers)
        log_mock.assert_called_once()
        args = log_mock.call_args[0]
        assert args[0] == "pause"
        assert args[1] == "b3"
