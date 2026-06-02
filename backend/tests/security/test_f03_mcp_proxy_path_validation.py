"""F-03 — MCP proxy must validate the {path} segment so URL-shaped or
traversal-shaped values cannot reach unintended hosts.

We can not exhaustively prove the absence of SSRF, but we can pin
defence-in-depth: reject paths containing `..`, NUL, scheme prefixes,
or unescaped double-slash.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


_BUYER = {
    "token": "tok-fwd",
    "vps_id": "concerto-abc",
    "vps_ip": "https://p01--concerto-abc--ns.code.run",
    "mcp_url": "https://p01--concerto-abc--ns.code.run/mcp",
    "bearer_token": "b",
    "status": "active",
    "plan": "solo",
    "runtime_state": None,
    "last_active_at": None,
}


def _app() -> FastAPI:
    from concerto.mcp_proxy_router import router as proxy_router
    app = FastAPI()
    app.include_router(proxy_router)
    return app


def _client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


def _mock_upstream():
    async def _aiter(chunk_size=4096):
        yield b'{"ok":true}'

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.aiter_bytes = _aiter
    mock_resp.aclose = AsyncMock()
    client = MagicMock()
    client.build_request = MagicMock(return_value=MagicMock())
    client.send = AsyncMock(return_value=mock_resp)
    client.aclose = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.parametrize("bad_path", [
    "..",
    "../etc/passwd",
    "..%2F..%2Fetc/passwd",
    "mcp/../../../admin",
    "%00",
    "mcp%00admin",
    "http://evil.example/x",
    "https://evil.example/x",
    "//evil.example/x",
])
def test_f03_dangerous_path_rejected(bad_path):
    """All listed payloads must NOT be forwarded upstream."""
    import concerto.mcp_proxy_router as proxy_mod
    proxy_mod._rl_buckets.clear()

    upstream = _mock_upstream()
    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=_BUYER)),
        patch("concerto.db.update_buyer", AsyncMock()),
        patch.object(proxy_mod.httpx, "AsyncClient", return_value=upstream),
    ):
        client = _client()
        r = client.get(f"/mcp-proxy/tok-fwd/{bad_path}")

    # Reject with 4xx, do NOT 200-forward
    assert r.status_code in (400, 404), (
        f"path={bad_path!r} should have been rejected but got {r.status_code}"
    )
    # The upstream client must not have been sent the request.
    assert not upstream.send.called, (
        f"path={bad_path!r} reached the upstream forward path — SSRF risk"
    )


def test_f03_legitimate_path_still_forwarded():
    """Negative regression: the normal /mcp path still works."""
    import concerto.mcp_proxy_router as proxy_mod
    proxy_mod._rl_buckets.clear()

    upstream = _mock_upstream()
    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=_BUYER)),
        patch("concerto.db.update_buyer", AsyncMock()),
        patch.object(proxy_mod.httpx, "AsyncClient", return_value=upstream),
    ):
        client = _client()
        r = client.post("/mcp-proxy/tok-fwd/mcp", json={"method": "tools/list"})

    assert r.status_code == 200, f"benign path was rejected: {r.status_code}"
    assert upstream.send.called
