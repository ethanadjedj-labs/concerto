"""Unit tests for concerto.trial_provision_watcher (non-NF-probe paths).

Does NOT re-test _is_nf_row, _nf_public_url_from_buyer, _nf_http_probe, or
_nf_http_probe_and_recover — those are covered by test_nf_http_probe.py.

Covers:
  - _find_stuck_trials: DB query logic
  - _set_failed / _set_awaiting_oauth / _get_bearer_token: DB writes/reads
  - _ssh_probe: subprocess interaction (mocked)
  - _promote: tunnel URL priority ordering
  - _watch_once: fail-after-timeout path, SSH probe success/failure paths
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import time
from unittest.mock import AsyncMock, patch

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS concerto_buyers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        email TEXT,
        provider TEXT DEFAULT 'digitalocean',
        vps_id TEXT, vps_ip TEXT, cf_tunnel_id TEXT,
        mcp_url TEXT, bearer_token TEXT, ssh_keypair_private_path TEXT,
        status TEXT DEFAULT 'installing',
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
        token="watcher-tok", email="w@example.com", plan="trial",
        status="installing", vps_id="d-w1", vps_ip="1.2.3.4",
        ssh_keypair_private_path="/tmp/fake-key.pem",
        provisioned_at=now - 120, expires_at=now + 3600,
        cf_tunnel_id="", bearer_token="stored-bearer",
        mcp_url=None, failure_reason=None,
    )
    defaults.update(kw)
    cols = ", ".join(defaults)
    ph = ", ".join("?" * len(defaults))
    conn.execute(f"INSERT INTO concerto_buyers ({cols}) VALUES ({ph})", list(defaults.values()))
    conn.commit()


# ── _find_stuck_trials ────────────────────────────────────────────────────────

class TestFindStuckTrials:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def _run(self):
        import concerto.trial_provision_watcher as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            return m._find_stuck_trials()
        finally:
            m.DB_PATH = orig

    def test_old_installing_trial_found(self):
        _insert(self.conn, provisioned_at=int(time.time()) - 120)
        assert len(self._run()) == 1

    def test_fresh_installing_below_probe_threshold_excluded(self):
        _insert(self.conn, provisioned_at=int(time.time()) - 10)
        assert self._run() == []

    def test_non_trial_plan_excluded(self):
        _insert(self.conn, plan="solo", provisioned_at=int(time.time()) - 120)
        assert self._run() == []

    def test_non_installing_status_excluded(self):
        _insert(self.conn, status="awaiting_oauth", provisioned_at=int(time.time()) - 120)
        assert self._run() == []

    def test_bearer_token_field_returned(self):
        _insert(self.conn, bearer_token="mybearer", provisioned_at=int(time.time()) - 120)
        rows = self._run()
        assert rows[0]["bearer_token"] == "mybearer"


# ── _set_failed ───────────────────────────────────────────────────────────────

class TestSetFailed:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)
        _insert(self.conn, token="fail-tok", status="installing")

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def test_sets_provisioning_failed_with_reason(self):
        import concerto.trial_provision_watcher as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            m._set_failed("fail-tok", "timed out after 1500s")
        finally:
            m.DB_PATH = orig
        row = self.conn.execute(
            "SELECT status, failure_reason FROM concerto_buyers WHERE token='fail-tok'"
        ).fetchone()
        assert row[0] == "provisioning_failed"
        assert row[1] == "timed out after 1500s"


# ── _set_awaiting_oauth ───────────────────────────────────────────────────────

class TestSetAwaitingOauth:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)
        _insert(self.conn, token="promo-tok", status="installing")

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def test_sets_awaiting_oauth_fields(self):
        import concerto.trial_provision_watcher as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            m._set_awaiting_oauth(
                "promo-tok", "https://mcp.url/mcp", "bearer-xyz", "https://mcp.url/terminal"
            )
        finally:
            m.DB_PATH = orig
        row = self.conn.execute(
            "SELECT status, mcp_url, bearer_token, ttyd_public_url "
            "FROM concerto_buyers WHERE token='promo-tok'"
        ).fetchone()
        assert row[0] == "awaiting_oauth"
        assert row[1] == "https://mcp.url/mcp"
        assert row[2] == "bearer-xyz"
        assert row[3] == "https://mcp.url/terminal"

    def test_idempotent_already_promoted_row_not_overwritten(self):
        self.conn.execute(
            "UPDATE concerto_buyers SET status='awaiting_oauth', mcp_url='https://old.url/mcp' "
            "WHERE token='promo-tok'"
        )
        self.conn.commit()
        import concerto.trial_provision_watcher as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            m._set_awaiting_oauth("promo-tok", "https://new.url/mcp", "new-bearer", "ttyd")
        finally:
            m.DB_PATH = orig
        # WHERE status='installing' means already-promoted rows are untouched
        row = self.conn.execute(
            "SELECT mcp_url FROM concerto_buyers WHERE token='promo-tok'"
        ).fetchone()
        assert row[0] == "https://old.url/mcp"


# ── _get_bearer_token ─────────────────────────────────────────────────────────

class TestGetBearerToken:
    def setup_method(self):
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.path = f.name
        f.close()
        self.conn = _make_db(self.path)
        _insert(self.conn, token="bearer-tok", bearer_token="stored-xyz")

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def test_returns_stored_bearer(self):
        import concerto.trial_provision_watcher as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            result = m._get_bearer_token("bearer-tok")
        finally:
            m.DB_PATH = orig
        assert result == "stored-xyz"

    def test_missing_token_returns_empty_string(self):
        import concerto.trial_provision_watcher as m
        orig, m.DB_PATH = m.DB_PATH, self.path
        try:
            result = m._get_bearer_token("ghost-tok")
        finally:
            m.DB_PATH = orig
        assert result == ""


# ── _ssh_probe ────────────────────────────────────────────────────────────────

class TestSshProbe:
    class _Proc:
        def __init__(self, data: bytes):
            self._data = data
        async def communicate(self):
            return self._data, b""

    def _probe(self, stdout: bytes):
        import concerto.trial_provision_watcher as m
        proc = self._Proc(stdout)
        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
            return asyncio.run(m._ssh_probe("1.2.3.4", "/tmp/key.pem"))

    def test_active_ttyd_with_bearer_returns_dict(self):
        result = self._probe(b"active\nbearerABC\ntunnel.concerto.run\n")
        assert result is not None
        assert result["bearer"] == "bearerABC"
        assert result["tunnel_hostname"] == "tunnel.concerto.run"

    def test_inactive_ttyd_returns_none(self):
        assert self._probe(b"inactive\nbearerABC\ntunnel.concerto.run\n") is None

    def test_missing_bearer_returns_none(self):
        assert self._probe(b"active\nMISSING\ntunnel.concerto.run\n") is None

    def test_empty_bearer_returns_none(self):
        assert self._probe(b"active\n\ntunnel.concerto.run\n") is None

    def test_too_few_lines_returns_none(self):
        assert self._probe(b"active\n") is None

    def test_real_tunnel_url_in_fourth_line_parsed(self):
        result = self._probe(
            b"active\nbearerXYZ\n\nhttps://random.trycloudflare.com\n"
        )
        assert result is not None
        assert result["real_tunnel_url"] == "https://random.trycloudflare.com"

    def test_timeout_returns_none(self):
        import concerto.trial_provision_watcher as m

        class _TimeoutProc:
            async def communicate(self):
                raise asyncio.TimeoutError()

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=_TimeoutProc())):
            result = asyncio.run(m._ssh_probe("1.2.3.4", "/tmp/key.pem"))
        assert result is None


# ── _promote ──────────────────────────────────────────────────────────────────

class TestPromote:
    def _buyer(self, token="promo"):
        return dict(token=token, email="p@x.com", expires_at=int(time.time()) + 3600)

    def test_named_tunnel_hostname_used_as_mcp_url(self):
        import concerto.trial_provision_watcher as m
        set_calls = []
        probe = dict(bearer="br", tunnel_hostname="c1234.concerto.run", real_tunnel_url="")
        with (
            patch.object(m, "_set_awaiting_oauth",
                         side_effect=lambda t, mu, b, tu: set_calls.append(mu)),
            patch("concerto.email_templates.trial_ready",
                  return_value={"subject": "s", "html": "h", "text": "t"}),
            patch("concerto.email_utils.send_email", new=AsyncMock()),
        ):
            asyncio.run(m._promote(self._buyer(), probe))
        assert set_calls == ["https://c1234.concerto.run"]

    def test_fallback_real_tunnel_url_used_when_no_hostname(self):
        import concerto.trial_provision_watcher as m
        set_calls = []
        probe = dict(bearer="br2", tunnel_hostname="",
                     real_tunnel_url="https://abc.trycloudflare.com")
        with (
            patch.object(m, "_set_awaiting_oauth",
                         side_effect=lambda t, mu, b, tu: set_calls.append(mu)),
            patch("concerto.email_templates.trial_ready",
                  return_value={"subject": "s", "html": "h", "text": "t"}),
            patch("concerto.email_utils.send_email", new=AsyncMock()),
        ):
            asyncio.run(m._promote(self._buyer(), probe))
        assert set_calls == ["https://abc.trycloudflare.com"]

    def test_no_tunnel_url_skips_promotion(self):
        import concerto.trial_provision_watcher as m
        set_calls = []
        probe = dict(bearer="br3", tunnel_hostname="", real_tunnel_url="")
        with patch.object(m, "_set_awaiting_oauth",
                          side_effect=lambda *a: set_calls.append(True)):
            asyncio.run(m._promote(self._buyer(), probe))
        assert set_calls == []


# ── _watch_once orchestration ─────────────────────────────────────────────────

class TestWatchOnce:
    def _buyer(self, **kw):
        now = int(time.time())
        b = dict(
            token="w-tok-1", email="w@x.com", vps_id="d-w1", vps_ip="1.2.3.4",
            ssh_keypair_private_path="",
            provisioned_at=now - 120, expires_at=now + 3600,
            cf_tunnel_id="", bearer_token="stored-bearer",
        )
        b.update(kw)
        return b

    def test_no_stuck_returns_zero(self):
        import concerto.trial_provision_watcher as m
        with patch.object(m, "_find_stuck_trials", return_value=[]):
            assert asyncio.run(m._watch_once()) == 0

    def test_fail_after_timeout_marks_failed(self):
        import concerto.trial_provision_watcher as m
        now = int(time.time())
        old = self._buyer(provisioned_at=now - (m._FAIL_AFTER_S + 100))
        failed = []
        with (
            patch.object(m, "_find_stuck_trials", return_value=[old]),
            patch.object(m, "_set_failed", side_effect=lambda t, r: failed.append(t)),
        ):
            asyncio.run(m._watch_once())
        assert "w-tok-1" in failed

    def test_ssh_probe_success_promotes_and_counts(self):
        import concerto.trial_provision_watcher as m
        now = int(time.time())
        # Create a real temp file so Path(key_path).exists() returns True
        kf = tempfile.NamedTemporaryFile(delete=False)
        kf.close()
        buyer = self._buyer(provisioned_at=now - 120, vps_ip="1.2.3.4",
                            ssh_keypair_private_path=kf.name)
        probe_result = dict(bearer="br", tunnel_hostname="c123.concerto.run", real_tunnel_url="")
        promoted = []
        try:
            with (
                patch.object(m, "_find_stuck_trials", return_value=[buyer]),
                patch.object(m, "_ssh_probe", new=AsyncMock(return_value=probe_result)),
                patch.object(m, "_promote",
                             new=AsyncMock(side_effect=lambda b, p: promoted.append(b["token"]))),
            ):
                count = asyncio.run(m._watch_once())
        finally:
            os.unlink(kf.name)
        assert count == 1
        assert "w-tok-1" in promoted

    def test_ssh_probe_failure_not_promoted(self):
        import concerto.trial_provision_watcher as m
        now = int(time.time())
        kf = tempfile.NamedTemporaryFile(delete=False)
        kf.close()
        buyer = self._buyer(provisioned_at=now - 120, vps_ip="1.2.3.4",
                            ssh_keypair_private_path=kf.name)
        promoted = []
        try:
            with (
                patch.object(m, "_find_stuck_trials", return_value=[buyer]),
                patch.object(m, "_ssh_probe", new=AsyncMock(return_value=None)),
                patch.object(m, "_promote",
                             new=AsyncMock(side_effect=lambda b, p: promoted.append(True))),
            ):
                count = asyncio.run(m._watch_once())
        finally:
            os.unlink(kf.name)
        assert count == 0
        assert promoted == []

    def test_missing_key_file_skipped(self):
        """No key file → buyer skipped (no SSH probe)."""
        import concerto.trial_provision_watcher as m
        now = int(time.time())
        buyer = self._buyer(provisioned_at=now - 120, vps_ip="1.2.3.4",
                            ssh_keypair_private_path="/nonexistent/key.pem")
        probe_calls = []
        with (
            patch.object(m, "_find_stuck_trials", return_value=[buyer]),
            patch.object(m, "_ssh_probe",
                         new=AsyncMock(side_effect=lambda *a: probe_calls.append(True))),
        ):
            asyncio.run(m._watch_once())
        assert probe_calls == []
