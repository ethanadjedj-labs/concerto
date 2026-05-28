"""Unit tests for the MCP wake-up proxy and related status_router changes.

Approach: mock concerto.db functions directly to avoid module-reload complexity.

Covers:
  - Unknown token → 404
  - No vps_ip → 503
  - Running service: forwarded without wake-up
  - Paused service: resume called, runtime_state cleared
  - Wake-up timeout → 504
  - Status router returns proxy URL for NF buyers, direct URL for DO buyers
"""
from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import concerto.mcp_proxy_router as proxy_mod
from concerto.mcp_proxy_router import router as proxy_router


# ── Shared buyer fixtures ─────────────────────────────────────────────────────

_RUNNING_BUYER = {
    "token": "tok-running",
    "provider": "northflank",
    "vps_id": "concerto-abc12345",
    "vps_ip": "https://p01--concerto-abc12345--ns.code.run",
    "mcp_url": "https://p01--concerto-abc12345--ns.code.run/mcp",
    "bearer_token": "testbearer",
    "status": "active",
    "plan": "solo",
    "runtime_state": None,
    "last_active_at": None,
}

_PAUSED_BUYER = {
    **_RUNNING_BUYER,
    "token": "tok-paused",
    "runtime_state": "paused",
}

_NO_VPS_BUYER = {
    **_RUNNING_BUYER,
    "token": "tok-no-vps",
    "vps_id": None,
    "vps_ip": None,
}


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(proxy_router)
    return app


def _client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


# ── Mock httpx upstream ───────────────────────────────────────────────────────

def _mock_upstream(status: int = 200, body: bytes = b'{"ok":true}'):
    async def _aiter_bytes(chunk_size=4096):
        yield body

    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.aiter_bytes = _aiter_bytes
    mock_resp.aclose = AsyncMock()
    return mock_resp


def _mock_httpx_client(upstream_response):
    mock_client = MagicMock()
    mock_client.build_request = MagicMock(return_value=MagicMock())
    mock_client.send = AsyncMock(return_value=upstream_response)
    mock_client.aclose = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestMcpProxy:

    def test_unknown_token_returns_404(self):
        with patch("concerto.db.get_buyer", AsyncMock(return_value=None)):
            client = _client()
            r = client.get("/mcp-proxy/no-such-token/mcp")
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"

    def test_no_vps_ip_returns_404(self):
        """Anti-enumeration: not-provisioned should look identical to unknown_token (both 404)."""
        with patch("concerto.db.get_buyer", AsyncMock(return_value=_NO_VPS_BUYER)):
            client = _client()
            r = client.get("/mcp-proxy/tok-no-vps/mcp")
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"

    def test_running_service_forwarded_no_resume(self):
        """Running service is forwarded without calling provider.resume."""
        upstream = _mock_upstream()
        mock_client = _mock_httpx_client(upstream)

        with (
            patch("concerto.db.get_buyer", AsyncMock(return_value=_RUNNING_BUYER)),
            patch("concerto.db.update_buyer", AsyncMock()),
            patch("concerto.provider_factory.resume", AsyncMock()) as mock_resume,
            patch.object(proxy_mod.httpx, "AsyncClient", return_value=mock_client),
        ):
            client = _client()
            r = client.post("/mcp-proxy/tok-running/mcp", json={"method": "tools/list"})

        mock_resume.assert_not_called()
        assert r.status_code == 200

    def test_paused_service_calls_resume(self):
        """Paused service: resume called and runtime_state cleared via update_buyer."""
        upstream = _mock_upstream()
        mock_client = _mock_httpx_client(upstream)
        update_calls: list = []

        async def fake_update(token, **fields):
            update_calls.append((token, fields))

        with (
            patch("concerto.db.get_buyer", AsyncMock(return_value=_PAUSED_BUYER)),
            patch("concerto.db.update_buyer", AsyncMock(side_effect=fake_update)),
            patch("concerto.provider_factory.resume", AsyncMock()),
            patch("concerto.mcp_proxy_router._poll_healthz", AsyncMock(return_value=True)),
            patch.object(proxy_mod.httpx, "AsyncClient", return_value=mock_client),
        ):
            client = _client()
            r = client.post("/mcp-proxy/tok-paused/mcp", json={"method": "tools/list"})

        # runtime_state must be cleared by wake-up
        wake_clear = [
            (tok, flds) for tok, flds in update_calls
            if flds.get("runtime_state") is None and "last_active_at" not in flds
        ]
        assert len(wake_clear) == 1, f"Expected one runtime_state=None update, got: {update_calls}"
        assert wake_clear[0][0] == "tok-paused"

    def test_paused_service_resume_then_forward(self):
        """After wake-up, the request is still forwarded to the upstream."""
        upstream = _mock_upstream(200, b'{"forwarded": true}')
        mock_client = _mock_httpx_client(upstream)

        with (
            patch("concerto.db.get_buyer", AsyncMock(return_value=_PAUSED_BUYER)),
            patch("concerto.db.update_buyer", AsyncMock()),
            patch("concerto.provider_factory.resume", AsyncMock()),
            patch("concerto.mcp_proxy_router._poll_healthz", AsyncMock(return_value=True)),
            patch.object(proxy_mod.httpx, "AsyncClient", return_value=mock_client),
        ):
            client = _client()
            r = client.post("/mcp-proxy/tok-paused/mcp", json={})

        assert r.status_code == 200
        assert r.json() == {"forwarded": True}

    def test_wake_timeout_returns_504(self):
        """If /healthz never responds, return 504 without forwarding."""
        with (
            patch("concerto.db.get_buyer", AsyncMock(return_value=_PAUSED_BUYER)),
            patch("concerto.db.update_buyer", AsyncMock()),
            patch("concerto.provider_factory.resume", AsyncMock()),
            patch("concerto.mcp_proxy_router._poll_healthz", AsyncMock(return_value=False)),
        ):
            client = _client()
            r = client.post("/mcp-proxy/tok-paused/mcp", json={})

        assert r.status_code == 504
        assert r.json()["error"] == "wake_timeout"

    def test_last_active_at_updated_on_success(self):
        """Successful proxy call records last_active_at."""
        upstream = _mock_upstream()
        mock_client = _mock_httpx_client(upstream)
        update_calls: list = []

        async def fake_update(token, **fields):
            update_calls.append((token, fields))

        with (
            patch("concerto.db.get_buyer", AsyncMock(return_value=_RUNNING_BUYER)),
            patch("concerto.db.update_buyer", AsyncMock(side_effect=fake_update)),
            patch.object(proxy_mod.httpx, "AsyncClient", return_value=mock_client),
        ):
            client = _client()
            r = client.post("/mcp-proxy/tok-running/mcp", json={})

        activity_updates = [
            (tok, flds) for tok, flds in update_calls
            if "last_active_at" in flds
        ]
        assert len(activity_updates) >= 1
        assert activity_updates[0][0] == "tok-running"


class TestPollHealthz:
    """Unit tests for the _poll_healthz helper."""

    def test_returns_true_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch.object(proxy_mod.httpx, "AsyncClient", return_value=mock_client):
            result = asyncio.run(
                proxy_mod._poll_healthz("https://example.com/healthz", timeout_s=5)
            )
        assert result is True

    def test_returns_false_on_timeout(self):
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch.object(proxy_mod.httpx, "AsyncClient", return_value=mock_client):
            result = asyncio.run(
                proxy_mod._poll_healthz("https://example.com/healthz", timeout_s=0.1)
            )
        assert result is False


class TestStatusRouterProxyUrl:
    """Status router returns proxy URL for NF buyers, direct URL for DO."""

    def _build_client(self, buyer_data: dict) -> TestClient:
        with patch.dict(os.environ, {"CONCERTO_API_BASE": "https://api.concerto.run"}):
            import importlib
            import concerto.status_router as sr
            importlib.reload(sr)
            app = FastAPI()
            app.include_router(sr.router)

            with patch("concerto.db.get_buyer", AsyncMock(return_value=buyer_data)):
                with patch("concerto.db.update_buyer", AsyncMock()):
                    return TestClient(app), buyer_data["token"]

    def test_nf_buyer_gets_proxy_url(self):
        buyer = {
            "token": "tok-nf-proxy",
            "provider": "northflank",
            "status": "active",
            "plan": "solo",
            "mcp_url": "https://p01--concerto-abc--ns.code.run/mcp",
            "vps_ip": "https://p01--concerto-abc--ns.code.run",
            "bearer_token": "testbearer",
        }
        with patch.dict(os.environ, {"CONCERTO_API_BASE": "https://api.concerto.run"}):
            import importlib
            import concerto.status_router as sr
            importlib.reload(sr)
            app = FastAPI()
            app.include_router(sr.router)
            with (
                patch("concerto.db.get_buyer", AsyncMock(return_value=buyer)),
                patch("concerto.db.update_buyer", AsyncMock()),
            ):
                client = TestClient(app)
                r = client.get("/api/buyer/tok-nf-proxy/status")
        assert r.status_code == 200
        assert r.json()["mcp_url"] == "https://api.concerto.run/mcp-proxy/tok-nf-proxy/mcp"

    def test_do_buyer_gets_direct_url(self):
        buyer = {
            "token": "tok-do-direct",
            "provider": "digitalocean",
            "status": "active",
            "plan": "byoc",
            "mcp_url": "https://tunnel.example.com/mcp",
            "vps_ip": "1.2.3.4",
            "bearer_token": "testbearer",
        }
        with patch.dict(os.environ, {"CONCERTO_API_BASE": "https://api.concerto.run"}):
            import importlib
            import concerto.status_router as sr
            importlib.reload(sr)
            app = FastAPI()
            app.include_router(sr.router)
            with (
                patch("concerto.db.get_buyer", AsyncMock(return_value=buyer)),
                patch("concerto.db.update_buyer", AsyncMock()),
            ):
                client = TestClient(app)
                r = client.get("/api/buyer/tok-do-direct/status")
        assert r.status_code == 200
        assert r.json()["mcp_url"] == "https://tunnel.example.com/mcp"


class TestRateLimit:
    """In-memory per-buyer rate limiting."""

    def setup_method(self):
        # Clear buckets between tests
        from concerto import mcp_proxy_router
        mcp_proxy_router._rl_buckets.clear()

    def test_rate_limit_check_allows_under_threshold(self):
        from concerto.mcp_proxy_router import _rate_limit_check, _RL_MAX_PER_WINDOW
        for i in range(_RL_MAX_PER_WINDOW):
            assert _rate_limit_check("tok-a") is True

    def test_rate_limit_check_blocks_over_threshold(self):
        from concerto.mcp_proxy_router import _rate_limit_check, _RL_MAX_PER_WINDOW
        for i in range(_RL_MAX_PER_WINDOW):
            _rate_limit_check("tok-a")
        # The next one is blocked
        assert _rate_limit_check("tok-a") is False

    def test_rate_limit_is_per_buyer(self):
        from concerto.mcp_proxy_router import _rate_limit_check, _RL_MAX_PER_WINDOW
        # Fill bucket for tok-a
        for i in range(_RL_MAX_PER_WINDOW):
            _rate_limit_check("tok-a")
        # tok-b is unaffected
        assert _rate_limit_check("tok-b") is True

    def test_rate_limit_returns_429_in_handler(self):
        """End-to-end: hammer the proxy, expect 429 after limit."""
        from concerto.mcp_proxy_router import _RL_MAX_PER_WINDOW
        upstream = _mock_upstream()
        with patch("concerto.db.get_buyer", AsyncMock(return_value=_RUNNING_BUYER)), \
             patch("concerto.db.update_buyer", AsyncMock(return_value=None)), \
             patch("httpx.AsyncClient", return_value=upstream):
            client = _client()
            # Fill bucket
            for i in range(_RL_MAX_PER_WINDOW):
                client.get("/mcp-proxy/tok-rl/mcp")
            # Next call gets 429
            r = client.get("/mcp-proxy/tok-rl/mcp")
            assert r.status_code == 429
            assert r.json()["error"] == "rate_limited"
            assert "Retry-After" in r.headers
