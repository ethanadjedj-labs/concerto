"""Unit tests for concerto.hosted_lifecycle.

Covers:
  - _do_delete_droplet: routes to provider_factory.destroy_droplet
  - _do_power_off_droplet: routes to provider_factory.suspend; empty token returns False
  - _list_do_droplet_ids: httpx pagination, empty-api-key early-out, error handling
  - reconcile_external_destroys: grace window, already-destroyed skip, dry_run, do_api_unavailable
  - reconcile: grace_destroy_at path, past_due_suspend_at path, call to external reconcile
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_resp(status: int, json_data: dict | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data or {}
    r.raise_for_status = MagicMock()
    return r


def _make_async_client(get_responses: list | None = None,
                       post_responses: list | None = None) -> MagicMock:
    client = AsyncMock()
    if get_responses is not None:
        client.get = AsyncMock(side_effect=get_responses)
    if post_responses is not None:
        client.post = AsyncMock(side_effect=post_responses)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# ── _do_delete_droplet ────────────────────────────────────────────────────────

class TestDoDeleteDroplet:
    def test_valid_droplet_id_calls_factory_and_returns_true(self):
        import concerto.hosted_lifecycle as m
        with patch.object(m._provider, "destroy_droplet", new=AsyncMock()) as mock_d:
            result = asyncio.run(m._do_delete_droplet("droplet-999"))
        assert result is True
        mock_d.assert_called_once()
        _, kwargs = mock_d.call_args
        assert kwargs["vps_id"] == "droplet-999"

    def test_empty_droplet_id_returns_false(self):
        import concerto.hosted_lifecycle as m
        with patch.object(m._provider, "destroy_droplet", new=AsyncMock()) as mock_d:
            result = asyncio.run(m._do_delete_droplet(""))
        assert result is False
        mock_d.assert_not_called()

    def test_cf_tunnel_id_empty_in_factory_call(self):
        """CF tunnel cleanup is intentionally excluded — caller handles it."""
        import concerto.hosted_lifecycle as m
        calls = []
        async def capture(**kw):
            calls.append(kw)
        with patch.object(m._provider, "destroy_droplet", new=AsyncMock(side_effect=capture)):
            asyncio.run(m._do_delete_droplet("d-111"))
        assert calls[0]["cf_tunnel_id"] == ""


# ── _do_power_off_droplet ─────────────────────────────────────────────────────

class TestDoPowerOffDroplet:
    def test_with_token_and_id_calls_suspend(self):
        import concerto.hosted_lifecycle as m
        with (
            patch.object(m, "_CONCERTO_DO_API_TOKEN", "test-token"),
            patch.object(m._provider, "suspend", new=AsyncMock()) as mock_s,
        ):
            result = asyncio.run(m._do_power_off_droplet("d-222"))
        assert result is True
        mock_s.assert_called_once()

    def test_empty_droplet_id_returns_false(self):
        import concerto.hosted_lifecycle as m
        with patch.object(m, "_CONCERTO_DO_API_TOKEN", "test-token"):
            result = asyncio.run(m._do_power_off_droplet(""))
        assert result is False

    def test_empty_api_token_returns_false(self):
        import concerto.hosted_lifecycle as m
        with (
            patch.object(m, "_CONCERTO_DO_API_TOKEN", ""),
            patch.object(m._provider, "suspend", new=AsyncMock()) as mock_s,
        ):
            result = asyncio.run(m._do_power_off_droplet("d-333"))
        assert result is False
        mock_s.assert_not_called()


# ── _list_do_droplet_ids ──────────────────────────────────────────────────────

class TestListDoDropletIds:
    def test_empty_api_key_returns_none(self):
        import concerto.hosted_lifecycle as m
        result = asyncio.run(m._list_do_droplet_ids(""))
        assert result is None

    def test_single_page_returns_ids(self):
        import concerto.hosted_lifecycle as m
        page_resp = _mock_resp(200, {"droplets": [{"id": 101}, {"id": 202}]})
        page_resp.raise_for_status = MagicMock()
        mock_client = _make_async_client(get_responses=[page_resp])
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = asyncio.run(m._list_do_droplet_ids("api-key"))
        assert result == {"101", "202"}

    def test_http_error_returns_none(self):
        import concerto.hosted_lifecycle as m
        import httpx
        mock_client = _make_async_client()
        mock_client.get = AsyncMock(side_effect=Exception("connection error"))
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = asyncio.run(m._list_do_droplet_ids("api-key"))
        assert result is None


# ── reconcile_external_destroys ───────────────────────────────────────────────

class TestReconcileExternalDestroys:
    def _entry(self, **kw):
        now = int(time.time())
        e = dict(droplet_id="d-ext", buyer_token="bt-ext",
                 status="active", created_at=now - 700)
        e.update(kw)
        return e

    def test_do_api_unavailable_returns_error_key(self):
        import concerto.hosted_lifecycle as m
        with patch.object(m, "_list_do_droplet_ids", new=AsyncMock(return_value=None)):
            result = asyncio.run(m.reconcile_external_destroys())
        assert "do_api_unavailable" in result["errors"]
        assert result["reconciled"] == 0

    def test_destroyed_status_skipped(self):
        import concerto.hosted_lifecycle as m
        entry = self._entry(status="destroyed")
        with (
            patch.object(m, "_list_do_droplet_ids", new=AsyncMock(return_value=set())),
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
        ):
            result = asyncio.run(m.reconcile_external_destroys())
        assert result["reconciled"] == 0

    def test_grace_window_entry_skipped(self):
        import concerto.hosted_lifecycle as m
        now = int(time.time())
        entry = self._entry(created_at=now - 100)  # only 100 s old — within 600 s grace
        with (
            patch.object(m, "_list_do_droplet_ids", new=AsyncMock(return_value=set())),
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
        ):
            result = asyncio.run(m.reconcile_external_destroys())
        assert result["skipped"] == 1
        assert result["reconciled"] == 0

    def test_missing_droplet_outside_grace_reconciled(self):
        import concerto.hosted_lifecycle as m
        entry = self._entry()  # created 700 s ago, not in live_ids
        with (
            patch.object(m, "_list_do_droplet_ids", new=AsyncMock(return_value={"d-other"})),
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
            patch.object(m.db, "update_buyer", new=AsyncMock()),
            patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        ):
            result = asyncio.run(m.reconcile_external_destroys())
        assert result["reconciled"] == 1

    def test_dry_run_counts_but_no_db_writes(self):
        import concerto.hosted_lifecycle as m
        entry = self._entry()
        update_calls = []
        with (
            patch.object(m, "_list_do_droplet_ids", new=AsyncMock(return_value={"d-other"})),
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
            patch.object(m.db, "update_buyer",
                         new=AsyncMock(side_effect=lambda *a, **k: update_calls.append(True))),
            patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        ):
            result = asyncio.run(m.reconcile_external_destroys(dry_run=True))
        assert result["dry_run"] is True
        assert result["reconciled"] == 1
        assert update_calls == []  # no DB write in dry_run


# ── reconcile ────────────────────────────────────────────────────────────────

class TestReconcile:
    def _ext_result(self):
        return {"reconciled": 0, "skipped": 0, "errors": [], "dry_run": False}

    def test_grace_destroy_at_in_past_destroys_droplet(self):
        import concerto.hosted_lifecycle as m
        now = int(time.time())
        destroy_at = now - 60
        entry = dict(status=f"grace_destroy_at:{destroy_at}",
                     droplet_id="d-grace", buyer_token="bt-grace")
        with (
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
            patch.object(m, "_do_delete_droplet", new=AsyncMock(return_value=True)),
            patch.object(m.db, "get_buyer", new=AsyncMock(return_value={"cf_tunnel_id": ""})),
            patch.object(m.db, "update_buyer", new=AsyncMock()),
            patch.object(m, "reconcile_external_destroys",
                         new=AsyncMock(return_value=self._ext_result())),
            patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        ):
            result = asyncio.run(m.reconcile())
        assert result["destroyed"] == 1
        assert result["errors"] == []

    def test_grace_destroy_at_in_future_not_destroyed(self):
        import concerto.hosted_lifecycle as m
        now = int(time.time())
        entry = dict(status=f"grace_destroy_at:{now + 3600}",
                     droplet_id="d-future", buyer_token="bt-future")
        delete_calls = []
        with (
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
            patch.object(m, "_do_delete_droplet",
                         new=AsyncMock(side_effect=lambda d: delete_calls.append(d))),
            patch.object(m, "reconcile_external_destroys",
                         new=AsyncMock(return_value=self._ext_result())),
        ):
            result = asyncio.run(m.reconcile())
        assert result["destroyed"] == 0
        assert delete_calls == []

    def test_past_due_suspend_at_suspends(self):
        import concerto.hosted_lifecycle as m
        now = int(time.time())
        suspend_at = now - 60
        entry = dict(status=f"past_due_suspend_at:{suspend_at}",
                     droplet_id="d-suspend", buyer_token="bt-suspend")
        with (
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
            patch.object(m, "_do_power_off_droplet", new=AsyncMock(return_value=True)),
            patch.object(m.db, "update_hosted_pool_status", new=AsyncMock()),
            patch.object(m.db, "update_buyer", new=AsyncMock()),
            patch.object(m.db, "get_buyer",
                         new=AsyncMock(return_value={"email": "", "cf_tunnel_id": ""})),
            patch.object(m, "reconcile_external_destroys",
                         new=AsyncMock(return_value=self._ext_result())),
        ):
            result = asyncio.run(m.reconcile())
        assert result["suspended"] == 1

    def test_cf_tunnel_destroyed_on_grace_destroy(self):
        import concerto.hosted_lifecycle as m
        now = int(time.time())
        entry = dict(status=f"grace_destroy_at:{now - 60}",
                     droplet_id="d-cf", buyer_token="bt-cf")
        tunnel_calls = []
        with (
            patch.object(m.db, "get_hosted_pool_entries", new=AsyncMock(return_value=[entry])),
            patch.object(m, "_do_delete_droplet", new=AsyncMock(return_value=True)),
            patch.object(m.db, "get_buyer",
                         new=AsyncMock(return_value={"cf_tunnel_id": "tun-abc"})),
            patch.object(m, "destroy_named_tunnel",
                         new=AsyncMock(side_effect=lambda tid: tunnel_calls.append(tid))),
            patch.object(m.db, "update_buyer", new=AsyncMock()),
            patch.object(m, "reconcile_external_destroys",
                         new=AsyncMock(return_value=self._ext_result())),
            patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        ):
            asyncio.run(m.reconcile())
        assert "tun-abc" in tunnel_calls
