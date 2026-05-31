"""Unit tests for concerto.nf_orphan_reaper.

Covers:
  - _is_concerto_service / _is_concerto_volume: name matching
  - _classify_resource: buyer status routing
  - run_orphan_pass (dry_run=True): orphan detected → flagged, live resource → left alone
  - run_orphan_pass (dry_run=False): orphan → destroy called, live → skip
  - run_orphan_pass: safety double-check aborts destroy if buyer becomes live
  - run_orphan_pass: terminal buyer row → treated as orphan
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from concerto.nf_orphan_reaper import (
    LIVE_STATUSES,
    TERMINAL_STATUSES,
    _classify_resource,
    _is_concerto_service,
    _is_concerto_volume,
    run_orphan_pass,
)

# ── Minimal DB schema ──────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE concerto_buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    email TEXT,
    provider TEXT DEFAULT 'northflank',
    vps_id TEXT,
    status TEXT DEFAULT 'active',
    paid_at INTEGER
)
"""


def _make_db() -> tuple[str, sqlite3.Connection]:
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = f.name
    f.close()
    conn = sqlite3.connect(path)
    conn.execute(_SCHEMA)
    conn.commit()
    return path, conn


def _insert(conn: sqlite3.Connection, **kw) -> None:
    defaults = dict(
        token="tok12345", email="test@example.com",
        provider="northflank", vps_id="concerto-tok12345",
        status="active", paid_at=int(time.time()),
    )
    defaults.update(kw)
    cols = ", ".join(defaults)
    ph = ", ".join("?" * len(defaults))
    conn.execute(f"INSERT INTO concerto_buyers ({cols}) VALUES ({ph})", list(defaults.values()))
    conn.commit()


# ── Name matching ──────────────────────────────────────────────────────────────

class TestIsContertoService:
    def test_valid_name(self):
        assert _is_concerto_service("concerto-abc12345") is True

    def test_valid_name_with_dashes(self):
        assert _is_concerto_service("concerto-a1b2c3d4") is True

    def test_not_concerto_prefix(self):
        assert _is_concerto_service("other-abc12345") is False

    def test_suffix_too_long(self):
        assert _is_concerto_service("concerto-abc123456") is False  # 9 chars

    def test_bare_prefix(self):
        assert _is_concerto_service("concerto-") is False

    def test_uppercase_rejected(self):
        assert _is_concerto_service("concerto-ABC12345") is False


class TestIsContertoVolume:
    def test_valid_volume(self):
        assert _is_concerto_volume("cvol-abc12345") is True

    def test_not_cvol_prefix(self):
        assert _is_concerto_volume("vol-abc12345") is False

    def test_suffix_too_long(self):
        assert _is_concerto_volume("cvol-abc123456") is False

    def test_bare_prefix(self):
        assert _is_concerto_volume("cvol-") is False


# ── _classify_resource ─────────────────────────────────────────────────────────

class TestClassifyResource:
    def setup_method(self):
        self.path, self.conn = _make_db()

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def test_no_db_row_is_orphan(self):
        cls, buyer = _classify_resource("NF service concerto-missing1", "concerto-missing1", self.path)
        assert cls == "orphan"
        assert buyer is None

    def test_live_status_is_not_orphan(self):
        _insert(self.conn, token="live1111", vps_id="concerto-live1111", status="active")
        cls, buyer = _classify_resource("NF service concerto-live1111", "concerto-live1111", self.path)
        assert cls == "live"
        assert buyer is not None

    def test_terminal_status_is_orphan(self):
        _insert(self.conn, token="term1111", vps_id="concerto-term1111", status="trial_expired")
        cls, buyer = _classify_resource("NF service concerto-term1111", "concerto-term1111", self.path)
        assert cls == "orphan"
        assert buyer is not None
        assert buyer["status"] == "trial_expired"

    def test_refunded_status_is_orphan(self):
        _insert(self.conn, token="refd1111", vps_id="concerto-refd1111", status="refunded")
        cls, buyer = _classify_resource("NF service concerto-refd1111", "concerto-refd1111", self.path)
        assert cls == "orphan"

    def test_unknown_status_is_protected(self):
        _insert(self.conn, token="unkn1111", vps_id="concerto-unkn1111", status="some_mystery_status")
        cls, buyer = _classify_resource("NF service concerto-unkn1111", "concerto-unkn1111", self.path)
        assert cls == "protected"

    def test_mcp_active_is_live(self):
        _insert(self.conn, token="mcp11111", vps_id="concerto-mcp11111", status="mcp_active")
        cls, _ = _classify_resource("NF service concerto-mcp11111", "concerto-mcp11111", self.path)
        assert cls == "live"

    def test_do_provider_not_matched(self):
        """A buyer row with provider='digitalocean' for the same vps_id is NOT matched."""
        _insert(self.conn, token="do111111", vps_id="concerto-do111111",
                status="active", provider="digitalocean")
        cls, buyer = _classify_resource("NF service concerto-do111111", "concerto-do111111", self.path)
        # No northflank buyer row → orphan
        assert cls == "orphan"
        assert buyer is None


# ── run_orphan_pass ────────────────────────────────────────────────────────────

def _make_svc(name: str) -> dict:
    return {"name": name, "id": name, "billing": {"deploymentPlan": "nf-compute-200"}}


def _make_vol(name: str) -> dict:
    return {"name": name, "id": name, "spec": {"storageSize": 6144}}


class TestRunOrphanPassDryRun:
    """Dry-run mode: orphans are identified and logged, nothing is destroyed."""

    def setup_method(self):
        self.path, self.conn = _make_db()

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def _run(self, services, volumes, token: str = ""):
        import concerto.nf_orphan_reaper as m
        orig_token, m._NF_API_TOKEN = m._NF_API_TOKEN, token or "fake-token"
        try:
            with (
                patch.object(m, "_fetch_all_services", AsyncMock(return_value=services)),
                patch.object(m, "_fetch_all_volumes", AsyncMock(return_value=volumes)),
            ):
                return asyncio.run(m.run_orphan_pass(db_path=self.path, dry_run=True))
        finally:
            m._NF_API_TOKEN = orig_token

    def test_no_resources_no_orphans(self):
        result = self._run([], [])
        assert result["orphaned_services"] == []
        assert result["orphaned_volumes"] == []
        assert result["nf_services_total"] == 0

    def test_orphaned_service_no_db_row(self):
        """NF service with no DB entry is flagged as orphan in dry-run."""
        result = self._run(
            services=[_make_svc("concerto-abc12345")],
            volumes=[],
        )
        assert "concerto-abc12345" in result["orphaned_services"]
        assert result["destroyed_services"] == []  # dry_run: no destruction

    def test_orphaned_volume_no_db_row(self):
        """NF volume with no DB entry is flagged as orphan in dry-run."""
        result = self._run(
            services=[],
            volumes=[_make_vol("cvol-abc12345")],
        )
        assert "cvol-abc12345" in result["orphaned_volumes"]
        assert result["destroyed_volumes"] == []

    def test_live_buyer_resource_left_alone(self):
        """NF service that has a live buyer is NOT flagged."""
        _insert(self.conn, token="live1111", vps_id="concerto-live1111", status="active")
        result = self._run(
            services=[_make_svc("concerto-live1111")],
            volumes=[],
        )
        assert result["orphaned_services"] == []
        assert result["protected"] == []

    def test_terminal_buyer_service_flagged(self):
        """NF service with a terminal buyer row is treated as orphan."""
        _insert(self.conn, token="exp11111", vps_id="concerto-exp11111", status="trial_expired")
        result = self._run(
            services=[_make_svc("concerto-exp11111")],
            volumes=[],
        )
        assert "concerto-exp11111" in result["orphaned_services"]

    def test_unknown_status_buyer_protected_not_orphaned(self):
        """NF service with unknown buyer status goes to protected, not orphaned."""
        _insert(self.conn, token="unk11111", vps_id="concerto-unk11111", status="mystery_status")
        result = self._run(
            services=[_make_svc("concerto-unk11111")],
            volumes=[],
        )
        assert result["orphaned_services"] == []
        assert "concerto-unk11111" in result["protected"]

    def test_non_concerto_service_ignored(self):
        """Services not matching the concerto-XXXXXXXX pattern are ignored."""
        result = self._run(
            services=[
                _make_svc("some-other-service"),
                _make_svc("concerto-toolongname"),  # 12-char suffix → ignored
            ],
            volumes=[],
        )
        assert result["orphaned_services"] == []

    def test_volume_matched_via_service_lookup(self):
        """Volume cvol-XXXXXXXX is checked against concerto-XXXXXXXX service."""
        _insert(self.conn, token="live1111", vps_id="concerto-live1111", status="active")
        result = self._run(
            services=[],
            volumes=[_make_vol("cvol-live1111")],  # live buyer → leave alone
        )
        assert result["orphaned_volumes"] == []

    def test_dry_run_flag_in_summary(self):
        result = self._run([], [])
        assert result["dry_run"] is True


class TestRunOrphanPassLive:
    """Live mode: orphaned resources are actually destroyed."""

    def setup_method(self):
        self.path, self.conn = _make_db()

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.path)

    def _run(self, services, volumes, destroy_svc_effect=None, destroy_vol_effect=None):
        import concerto.nf_orphan_reaper as m
        orig_token, m._NF_API_TOKEN = m._NF_API_TOKEN, "fake-token"
        destroy_svc_mock = AsyncMock(side_effect=destroy_svc_effect)
        destroy_vol_mock = AsyncMock(side_effect=destroy_vol_effect)
        try:
            with (
                patch.object(m, "_fetch_all_services", AsyncMock(return_value=services)),
                patch.object(m, "_fetch_all_volumes", AsyncMock(return_value=volumes)),
                patch.object(m, "_destroy_service", destroy_svc_mock),
                patch.object(m, "_destroy_volume", destroy_vol_mock),
            ):
                result = asyncio.run(m.run_orphan_pass(db_path=self.path, dry_run=False))
                return result, destroy_svc_mock, destroy_vol_mock
        finally:
            m._NF_API_TOKEN = orig_token

    def test_orphaned_service_is_destroyed(self):
        """Orphaned service (no DB row) is destroyed in live mode."""
        result, svc_mock, _ = self._run(
            services=[_make_svc("concerto-orph1234")],
            volumes=[],
        )
        assert "concerto-orph1234" in result["destroyed_services"]
        svc_mock.assert_called_once()

    def test_live_buyer_service_not_destroyed(self):
        """Service with live buyer is NOT destroyed."""
        _insert(self.conn, token="live1111", vps_id="concerto-live1111", status="active")
        result, svc_mock, _ = self._run(
            services=[_make_svc("concerto-live1111")],
            volumes=[],
        )
        assert result["destroyed_services"] == []
        svc_mock.assert_not_called()

    def test_destroy_failure_recorded_in_errors(self):
        """If destroy throws, error is recorded and pass continues."""
        result, _, _ = self._run(
            services=[_make_svc("concerto-fail1234")],
            volumes=[],
            destroy_svc_effect=RuntimeError("NF 500"),
        )
        assert result["destroyed_services"] == []
        assert len(result["errors"]) == 1
        assert "destroy_service" in result["errors"][0]

    def test_orphaned_volume_is_destroyed(self):
        """Orphaned volume (no corresponding DB buyer) is destroyed."""
        result, _, vol_mock = self._run(
            services=[],
            volumes=[_make_vol("cvol-orph1234")],
        )
        assert "cvol-orph1234" in result["destroyed_volumes"]
        vol_mock.assert_called_once()

    def test_safety_abort_when_buyer_becomes_live(self):
        """Safety double-check: if buyer turns live between scan and destroy, abort."""
        # Insert a buyer AFTER scanning but before destruction by patching _get_buyer_by_vps_id
        import concerto.nf_orphan_reaper as m
        orig_token, m._NF_API_TOKEN = m._NF_API_TOKEN, "fake-token"

        call_count = [0]

        def _mock_buyer(vps_id, db_path=""):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # first call (scan phase) → orphan
            # second call (pre-destroy double-check) → buyer is now live
            return {"token": "tok11111", "status": "active", "email": "test@x.com"}

        destroy_mock = AsyncMock()
        try:
            with (
                patch.object(m, "_fetch_all_services",
                             AsyncMock(return_value=[_make_svc("concerto-tok11111")])),
                patch.object(m, "_fetch_all_volumes", AsyncMock(return_value=[])),
                patch.object(m, "_get_buyer_by_vps_id", side_effect=_mock_buyer),
                patch.object(m, "_destroy_service", destroy_mock),
            ):
                result = asyncio.run(m.run_orphan_pass(db_path=self.path, dry_run=False))
        finally:
            m._NF_API_TOKEN = orig_token

        destroy_mock.assert_not_called()
        assert result["destroyed_services"] == []
        assert "concerto-tok11111" in result["protected"]

    def test_no_token_returns_error(self):
        """Missing API token returns error dict without crashing."""
        import concerto.nf_orphan_reaper as m
        orig, m._NF_API_TOKEN = m._NF_API_TOKEN, ""
        try:
            result = asyncio.run(m.run_orphan_pass(db_path=self.path, dry_run=True))
        finally:
            m._NF_API_TOKEN = orig
        assert result.get("error") == "no_token"
