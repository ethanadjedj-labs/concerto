"""Tests for auto-pause/resume lifecycle.

Covers:
  - Pause selection logic (which buyers get paused)
  - Resume endpoint: success, timeout, already-running, no VPS
  - Activity recording endpoint
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import time
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE concerto_buyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            email TEXT,
            stripe_session_id TEXT,
            provider TEXT DEFAULT 'northflank',
            region TEXT, vps_size TEXT, vps_id TEXT, vps_ip TEXT,
            mcp_url TEXT, bearer_token TEXT, ssh_keypair_private_path TEXT,
            status TEXT, paid_at INTEGER, provisioned_at INTEGER,
            installed_at INTEGER, plan TEXT DEFAULT 'solo',
            subscription_id TEXT, subscription_status TEXT, next_renewal_at INTEGER,
            stripe_customer_id TEXT, ttyd_public_url TEXT, ttyd_password TEXT,
            dashboard_opened_at INTEGER, last_active_at INTEGER,
            runtime_state TEXT, cf_tunnel_id TEXT,
            expires_at INTEGER, github_token TEXT, pre_expiry_warned_at INTEGER,
            failure_reason TEXT, drip_sent_at INTEGER
        )
    """)
    conn.commit()
    return conn


def _insert_buyer(conn: sqlite3.Connection, **kwargs) -> None:
    defaults = {
        "token": "test-token-123",
        "email": "test@example.com",
        "provider": "northflank",
        "vps_id": "svc-abc123",
        "status": "active",
        "plan": "solo",
        "runtime_state": None,
        "last_active_at": None,
        "ttyd_public_url": "https://p01--svc-abc123--ns.code.run",
    }
    defaults.update(kwargs)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join("?" * len(defaults))
    conn.execute(
        f"INSERT INTO concerto_buyers ({cols}) VALUES ({placeholders})",
        list(defaults.values()),
    )
    conn.commit()


# ── Pause selection logic ─────────────────────────────────────────────────────

class TestPauseSelectionLogic:
    """Tests for nf_auto_pause._get_eligible_buyers."""

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.conn = _make_db(self.db_path)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.db_path)

    def _eligible(self, now: int | None = None) -> list[dict]:
        import importlib
        with patch.dict(os.environ, {"CONCERTO_DB_PATH": self.db_path}):
            # Re-import to pick up patched env
            import concerto.nf_auto_pause as m
            importlib.reload(m)
            return m._get_eligible_buyers(now or int(time.time()))

    def test_active_buyer_idle_is_eligible(self):
        now = int(time.time())
        idle_at = now - 3600  # 60 min idle
        _insert_buyer(self.conn, status="active", last_active_at=idle_at)
        result = self._eligible(now)
        assert len(result) == 1
        assert result[0]["token"] == "test-token-123"

    def test_installing_buyer_never_eligible(self):
        now = int(time.time())
        _insert_buyer(self.conn, status="installing", last_active_at=now - 3600)
        assert self._eligible(now) == []

    def test_awaiting_oauth_never_eligible(self):
        now = int(time.time())
        _insert_buyer(self.conn, status="awaiting_oauth", last_active_at=now - 3600)
        assert self._eligible(now) == []

    def test_recently_active_not_eligible(self):
        now = int(time.time())
        _insert_buyer(self.conn, status="active", last_active_at=now - 60)  # 1 min ago
        assert self._eligible(now) == []

    def test_already_paused_not_eligible(self):
        now = int(time.time())
        _insert_buyer(
            self.conn,
            status="active",
            last_active_at=now - 3600,
            runtime_state="paused",
        )
        assert self._eligible(now) == []

    def test_null_last_active_at_not_eligible(self):
        now = int(time.time())
        _insert_buyer(self.conn, status="active", last_active_at=None)
        assert self._eligible(now) == []

    def test_no_vps_id_not_eligible(self):
        now = int(time.time())
        _insert_buyer(self.conn, status="active", last_active_at=now - 3600, vps_id=None)
        assert self._eligible(now) == []

    def test_digitalocean_provider_not_eligible(self):
        now = int(time.time())
        _insert_buyer(
            self.conn,
            status="active",
            last_active_at=now - 3600,
            provider="digitalocean",
        )
        assert self._eligible(now) == []

    def test_multiple_statuses_eligible(self):
        now = int(time.time())
        idle = now - 3600
        for i, status in enumerate(
            ["active", "oauth_complete", "mcp_active", "connector_first_call_detected"]
        ):
            _insert_buyer(
                self.conn,
                token=f"tok-{i}",
                status=status,
                last_active_at=idle,
            )
        result = self._eligible(now)
        assert len(result) == 4

    def test_dry_run_does_not_call_suspend(self):
        now = int(time.time())
        _insert_buyer(self.conn, status="active", last_active_at=now - 3600)

        suspend_calls = []

        async def fake_suspend(api_key, vps_id):
            suspend_calls.append(vps_id)

        with (
            patch.dict(os.environ, {
                "CONCERTO_DB_PATH": self.db_path,
                "CONCERTO_PAUSE_DRY_RUN": "1",
                "CONCERTO_PAUSE_AFTER_S": "1800",
            }),
            patch("concerto.provider_factory.suspend", fake_suspend),
        ):
            import concerto.nf_auto_pause as m
            import importlib
            importlib.reload(m)
            result = asyncio.run(m.run_pause_pass())

        assert result["dry_run"] is True
        assert result["paused"] == 1
        assert suspend_calls == []  # suspend was NOT called


# ── Activity endpoint ─────────────────────────────────────────────────────────

class TestActivityEndpoint:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.conn = _make_db(self.db_path)
        _insert_buyer(self.conn, token="act-tok-001", status="active")

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.db_path)

    def _client(self):
        with patch.dict(os.environ, {"CONCERTO_DB_PATH": self.db_path}):
            import importlib
            import concerto.db as db_mod
            importlib.reload(db_mod)
            from concerto.activity_router import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            return TestClient(app)

    def test_valid_activity_ping_updates_db(self):
        client = self._client()
        now = int(time.time())
        r = client.post(
            "/api/internal/activity?token=act-tok-001",
            json={"last_active_at": now, "ttyd_connected": True},
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

        row = self.conn.execute(
            "SELECT last_active_at FROM concerto_buyers WHERE token='act-tok-001'"
        ).fetchone()
        assert row[0] == now

    def test_unknown_token_returns_404(self):
        client = self._client()
        r = client.post(
            "/api/internal/activity?token=nobody",
            json={"last_active_at": time.time(), "ttyd_connected": False},
        )
        assert r.status_code == 404

    def test_missing_token_returns_422(self):
        client = self._client()
        r = client.post(
            "/api/internal/activity",
            json={"last_active_at": time.time(), "ttyd_connected": False},
        )
        assert r.status_code == 422


# ── Resume endpoint ───────────────────────────────────────────────────────────

class TestResumeEndpoint:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.conn = _make_db(self.db_path)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.db_path)

    def _client(self, extra_buyers: list[dict] | None = None):
        for b in (extra_buyers or []):
            _insert_buyer(self.conn, **b)
        with patch.dict(os.environ, {"CONCERTO_DB_PATH": self.db_path}):
            import importlib
            import concerto.db as db_mod
            importlib.reload(db_mod)
            from concerto.activity_router import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            return TestClient(app)

    def test_already_running_returns_200_noop(self):
        """Calling resume on a non-paused service is idempotent."""
        client = self._client([{
            "token": "res-tok-001",
            "status": "active",
            "vps_id": "svc-111",
            "runtime_state": None,
        }])
        r = client.post("/api/internal/resume?token=res-tok-001")
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["resumed"] is False

    def test_paused_service_is_resumed(self):
        """Paused service: resume called, runtime_state cleared."""
        _insert_buyer(
            self.conn,
            token="res-tok-002",
            status="active",
            vps_id="svc-222",
            runtime_state="paused",
            ttyd_public_url="https://p01--svc-222--ns.code.run",
        )

        async def fake_resume(api_key, vps_id):
            pass

        with (
            patch("concerto.provider_factory.resume", AsyncMock(side_effect=fake_resume)),
            patch(
                "concerto.activity_router._poll_healthz",
                AsyncMock(return_value=True),
            ),
            patch.dict(os.environ, {"CONCERTO_DB_PATH": self.db_path}),
        ):
            import importlib
            import concerto.db as db_mod
            importlib.reload(db_mod)
            from concerto.activity_router import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            r = client.post("/api/internal/resume?token=res-tok-002")

        assert r.status_code == 200
        assert r.json()["resumed"] is True

        row = self.conn.execute(
            "SELECT runtime_state FROM concerto_buyers WHERE token='res-tok-002'"
        ).fetchone()
        assert row[0] is None

    def test_healthz_timeout_returns_504(self):
        """If /healthz never responds, return 504."""
        _insert_buyer(
            self.conn,
            token="res-tok-003",
            status="active",
            vps_id="svc-333",
            runtime_state="paused",
            ttyd_public_url="https://p01--svc-333--ns.code.run",
        )
        with (
            patch("concerto.provider_factory.resume", AsyncMock()),
            patch(
                "concerto.activity_router._poll_healthz",
                AsyncMock(return_value=False),
            ),
            patch.dict(os.environ, {"CONCERTO_DB_PATH": self.db_path}),
        ):
            import importlib
            import concerto.db as db_mod
            importlib.reload(db_mod)
            from concerto.activity_router import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            r = client.post("/api/internal/resume?token=res-tok-003")

        assert r.status_code == 504

    def test_no_vps_id_returns_409(self):
        _insert_buyer(
            self.conn,
            token="res-tok-004",
            status="active",
            vps_id=None,
            runtime_state="paused",
        )
        with patch.dict(os.environ, {"CONCERTO_DB_PATH": self.db_path}):
            import importlib
            import concerto.db as db_mod
            importlib.reload(db_mod)
            from concerto.activity_router import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            r = client.post("/api/internal/resume?token=res-tok-004")
        assert r.status_code == 409

    def test_unknown_token_returns_404(self):
        client = self._client()
        r = client.post("/api/internal/resume?token=ghost")
        assert r.status_code == 404
