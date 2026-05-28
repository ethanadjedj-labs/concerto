"""
Unit tests for the NF HTTP probe fallback in trial_provision_watcher.

Tests:
  (a) probe success  → DB row updated to awaiting_oauth
  (b) probe failure  → DB row unchanged
  (c) idempotency    → already-promoted row not double-updated
  (d) max_age gating → rows younger than max_age are skipped
"""
from __future__ import annotations

import os
import sys
import sqlite3
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# Allow importing from backend/concerto without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_buyer(
    token: str = "testtoken",
    status: str = "installing",
    provisioned_at: int | None = None,
    vps_ip: str = "https://p01--concerto-testto--w4lp2d6pgkf6.code.run",
    bearer_token: str = "testbearer123",
    age_s: int = 300,
) -> dict:
    now = int(time.time())
    return {
        "token": token,
        "email": "test@example.com",
        "vps_id": "concerto-testto",
        "vps_ip": vps_ip,
        "ssh_keypair_private_path": "",
        "provisioned_at": provisioned_at if provisioned_at is not None else (now - age_s),
        "expires_at": now + 3600,
        "cf_tunnel_id": "",
        "plan": "trial",
        "bearer_token": bearer_token,
    }


def _setup_db(db_path: str, buyer: dict) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS concerto_buyers (
            token TEXT PRIMARY KEY,
            email TEXT,
            vps_id TEXT,
            vps_ip TEXT,
            ssh_keypair_private_path TEXT,
            provisioned_at INTEGER,
            expires_at INTEGER,
            cf_tunnel_id TEXT,
            plan TEXT,
            status TEXT,
            bearer_token TEXT,
            mcp_url TEXT,
            ttyd_public_url TEXT,
            installed_at INTEGER,
            failure_reason TEXT
        )
    """)
    conn.execute("""
        INSERT INTO concerto_buyers
          (token, email, vps_id, vps_ip, ssh_keypair_private_path,
           provisioned_at, expires_at, cf_tunnel_id, plan, status, bearer_token)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        buyer["token"], buyer["email"], buyer["vps_id"], buyer["vps_ip"],
        buyer["ssh_keypair_private_path"], buyer["provisioned_at"],
        buyer["expires_at"], buyer["cf_tunnel_id"], buyer["plan"],
        "installing", buyer["bearer_token"],
    ))
    conn.commit()
    conn.close()


def _read_buyer_status(db_path: str, token: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT status, mcp_url, ttyd_public_url, bearer_token FROM concerto_buyers WHERE token=?",
        (token,),
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestNfIsRow:
    def test_https_url_is_nf(self):
        from concerto.trial_provision_watcher import _is_nf_row
        buyer = _make_buyer(vps_ip="https://p01--svc--ns.code.run")
        assert _is_nf_row(buyer) is True

    def test_plain_ip_is_not_nf(self):
        from concerto.trial_provision_watcher import _is_nf_row
        buyer = _make_buyer(vps_ip="1.2.3.4")
        assert _is_nf_row(buyer) is False

    def test_empty_vps_ip_is_not_nf(self):
        from concerto.trial_provision_watcher import _is_nf_row
        buyer = _make_buyer(vps_ip="")
        assert _is_nf_row(buyer) is False


class TestNfPublicUrl:
    def test_strips_trailing_slash(self):
        from concerto.trial_provision_watcher import _nf_public_url_from_buyer
        buyer = _make_buyer(vps_ip="https://p01--svc--ns.code.run/")
        assert _nf_public_url_from_buyer(buyer) == "https://p01--svc--ns.code.run"

    def test_returns_vps_ip_as_url(self):
        from concerto.trial_provision_watcher import _nf_public_url_from_buyer
        buyer = _make_buyer(vps_ip="https://p01--concerto-abc--ns.code.run")
        assert _nf_public_url_from_buyer(buyer) == "https://p01--concerto-abc--ns.code.run"


class TestNfHttpProbeSuccess:
    """(a) Probe returns 200 → DB updated to awaiting_oauth."""

    def test_probe_success_updates_db(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        buyer = _make_buyer(age_s=300)
        _setup_db(db_path, buyer)

        import concerto.trial_provision_watcher as watcher
        orig_db = watcher.DB_PATH
        orig_enabled = watcher._NF_HTTP_PROBE_ENABLED
        orig_max_age = watcher._NF_HTTP_PROBE_MAX_AGE_S
        watcher.DB_PATH = db_path
        watcher._NF_HTTP_PROBE_ENABLED = True
        watcher._NF_HTTP_PROBE_MAX_AGE_S = 180

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        async def run():
            with patch("concerto.trial_provision_watcher._nf_http_probe", new=AsyncMock(return_value=True)):
                return await watcher._nf_http_probe_and_recover(buyer, age=300)

        result = asyncio.run(run())

        watcher.DB_PATH = orig_db
        watcher._NF_HTTP_PROBE_ENABLED = orig_enabled
        watcher._NF_HTTP_PROBE_MAX_AGE_S = orig_max_age

        assert result is True
        row = _read_buyer_status(db_path, buyer["token"])
        assert row["status"] == "awaiting_oauth"
        assert row["mcp_url"] == "https://p01--concerto-testto--w4lp2d6pgkf6.code.run/mcp"
        assert row["ttyd_public_url"] == "https://p01--concerto-testto--w4lp2d6pgkf6.code.run"
        assert row["bearer_token"] == "testbearer123"


class TestNfHttpProbeFailure:
    """(b) Probe returns non-200 → DB unchanged."""

    def test_probe_failure_leaves_db_unchanged(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        buyer = _make_buyer(age_s=300)
        _setup_db(db_path, buyer)

        import concerto.trial_provision_watcher as watcher
        orig_db = watcher.DB_PATH
        orig_enabled = watcher._NF_HTTP_PROBE_ENABLED
        orig_max_age = watcher._NF_HTTP_PROBE_MAX_AGE_S
        watcher.DB_PATH = db_path
        watcher._NF_HTTP_PROBE_ENABLED = True
        watcher._NF_HTTP_PROBE_MAX_AGE_S = 180

        async def run():
            with patch("concerto.trial_provision_watcher._nf_http_probe", new=AsyncMock(return_value=False)):
                return await watcher._nf_http_probe_and_recover(buyer, age=300)

        result = asyncio.run(run())

        watcher.DB_PATH = orig_db
        watcher._NF_HTTP_PROBE_ENABLED = orig_enabled
        watcher._NF_HTTP_PROBE_MAX_AGE_S = orig_max_age

        assert result is False
        row = _read_buyer_status(db_path, buyer["token"])
        assert row["status"] == "installing"
        assert row["mcp_url"] is None


class TestNfHttpProbeIdempotency:
    """(c) Row already in awaiting_oauth → DB update WHERE clause no-ops."""

    def test_already_promoted_row_not_double_updated(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        buyer = _make_buyer(age_s=300)
        _setup_db(db_path, buyer)

        # Manually promote the row to simulate a completed callback
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE concerto_buyers SET status='awaiting_oauth', mcp_url='https://already.set/mcp' WHERE token=?",
            (buyer["token"],),
        )
        conn.commit()
        conn.close()

        import concerto.trial_provision_watcher as watcher
        orig_db = watcher.DB_PATH
        orig_enabled = watcher._NF_HTTP_PROBE_ENABLED
        orig_max_age = watcher._NF_HTTP_PROBE_MAX_AGE_S
        watcher.DB_PATH = db_path
        watcher._NF_HTTP_PROBE_ENABLED = True
        watcher._NF_HTTP_PROBE_MAX_AGE_S = 180

        async def run():
            with patch("concerto.trial_provision_watcher._nf_http_probe", new=AsyncMock(return_value=True)):
                return await watcher._nf_http_probe_and_recover(buyer, age=300)

        result = asyncio.run(run())

        watcher.DB_PATH = orig_db
        watcher._NF_HTTP_PROBE_ENABLED = orig_enabled
        watcher._NF_HTTP_PROBE_MAX_AGE_S = orig_max_age

        # _set_awaiting_oauth uses WHERE status='installing'; already-promoted row is untouched.
        row = _read_buyer_status(db_path, buyer["token"])
        assert row["status"] == "awaiting_oauth"
        assert row["mcp_url"] == "https://already.set/mcp"


class TestNfHttpProbeMaxAgeGating:
    """(d) Rows younger than max_age are skipped regardless of probe result."""

    def test_young_row_skipped(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        buyer = _make_buyer(age_s=50)  # 50s old — much less than 180s max_age
        _setup_db(db_path, buyer)

        import concerto.trial_provision_watcher as watcher
        orig_db = watcher.DB_PATH
        orig_enabled = watcher._NF_HTTP_PROBE_ENABLED
        orig_max_age = watcher._NF_HTTP_PROBE_MAX_AGE_S
        watcher.DB_PATH = db_path
        watcher._NF_HTTP_PROBE_ENABLED = True
        watcher._NF_HTTP_PROBE_MAX_AGE_S = 180

        probe_called = []

        async def mock_probe(url, bearer):
            probe_called.append(url)
            return True

        async def run():
            with patch("concerto.trial_provision_watcher._nf_http_probe", new=AsyncMock(side_effect=mock_probe)):
                return await watcher._nf_http_probe_and_recover(buyer, age=50)

        result = asyncio.run(run())

        watcher.DB_PATH = orig_db
        watcher._NF_HTTP_PROBE_ENABLED = orig_enabled
        watcher._NF_HTTP_PROBE_MAX_AGE_S = orig_max_age

        assert result is False
        assert len(probe_called) == 0  # probe never fired
        row = _read_buyer_status(db_path, buyer["token"])
        assert row["status"] == "installing"

    def test_old_row_probed(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        buyer = _make_buyer(age_s=200)  # 200s old — over the 180s threshold
        _setup_db(db_path, buyer)

        import concerto.trial_provision_watcher as watcher
        orig_db = watcher.DB_PATH
        orig_enabled = watcher._NF_HTTP_PROBE_ENABLED
        orig_max_age = watcher._NF_HTTP_PROBE_MAX_AGE_S
        watcher.DB_PATH = db_path
        watcher._NF_HTTP_PROBE_ENABLED = True
        watcher._NF_HTTP_PROBE_MAX_AGE_S = 180

        probe_called = []

        async def mock_probe(url, bearer):
            probe_called.append(url)
            return False  # probe fails — just confirming it was called

        async def run():
            with patch("concerto.trial_provision_watcher._nf_http_probe", new=AsyncMock(side_effect=mock_probe)):
                return await watcher._nf_http_probe_and_recover(buyer, age=200)

        result = asyncio.run(run())

        watcher.DB_PATH = orig_db
        watcher._NF_HTTP_PROBE_ENABLED = orig_enabled
        watcher._NF_HTTP_PROBE_MAX_AGE_S = orig_max_age

        assert result is False
        assert len(probe_called) == 1  # probe was called


class TestNfHttpProbeDisabled:
    """Feature flag off → probe never fires."""

    def test_disabled_skips_all(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        buyer = _make_buyer(age_s=300)
        _setup_db(db_path, buyer)

        import concerto.trial_provision_watcher as watcher
        orig_db = watcher.DB_PATH
        orig_enabled = watcher._NF_HTTP_PROBE_ENABLED
        watcher.DB_PATH = db_path
        watcher._NF_HTTP_PROBE_ENABLED = False

        probe_called = []

        async def mock_probe(url, bearer):
            probe_called.append(url)
            return True

        async def run():
            with patch("concerto.trial_provision_watcher._nf_http_probe", new=AsyncMock(side_effect=mock_probe)):
                return await watcher._nf_http_probe_and_recover(buyer, age=300)

        result = asyncio.run(run())

        watcher.DB_PATH = orig_db
        watcher._NF_HTTP_PROBE_ENABLED = orig_enabled

        assert result is False
        assert len(probe_called) == 0
