"""Regression tests for RFC 9207 `iss` parameter in /authorize endpoint.

RFC 9207 (OAuth 2.0 Authorization Server Issuer Identification) requires the
authorization response to include `iss` equal to the AS's issuer URL. Without
it, a mix-up attack can redirect the authorization code to a malicious server.

Bug fixed: the /authorize redirect was missing `iss`, causing Claude Code
(which validates the AS metadata) to reject the authorization flow.

These tests guard the mcp_server.py authorize handler in installer/.
"""
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── Bootstrap — mock heavy deps before mcp_server is imported ─────────────────

_MOCK_MCP = MagicMock()
_MOCK_MCP.tool = lambda **kw: (lambda f: f)
for _mod in (
    "mcp",
    "mcp.server",
    "mcp.server.fastmcp",
    "mcp.server.transport_security",
    "uvicorn",
):
    sys.modules.setdefault(_mod, MagicMock())

sys.modules["mcp.server.fastmcp"].FastMCP = MagicMock(return_value=_MOCK_MCP)
sys.modules["mcp.server.transport_security"].TransportSecuritySettings = MagicMock

_INSTALLER_DIR = str(Path(__file__).parents[2] / "installer")
if _INSTALLER_DIR not in sys.path:
    sys.path.insert(0, _INSTALLER_DIR)

import mcp_server  # noqa: E402


# ── Mock request helper ────────────────────────────────────────────────────────


class _FakeRequest:
    """Minimal Starlette Request stand-in for authorize() unit tests."""

    def __init__(self, params: dict, host: str = "mcp.concerto.run", proto: str = "https"):
        self.query_params = params
        self.headers = {
            "host": host,
            "x-forwarded-proto": proto,
            "x-forwarded-host": host,
        }


_VALID_PARAMS = {
    "client_id": "test-client",
    "redirect_uri": "https://claude.ai/callback",
    "code_challenge": "abc" * 15,
    "code_challenge_method": "S256",
    "response_type": "code",
    "state": "random-state-xyz",
}


@pytest.fixture(autouse=True)
def _patch_clients(monkeypatch):
    """Empty client registry → any client_id is accepted (bootstrapping mode)."""
    monkeypatch.setattr(mcp_server, "_load_json", lambda p: {})


# ── RFC 9207: iss must be in the redirect URL ─────────────────────────────────


@pytest.mark.asyncio
async def test_authorize_redirect_contains_iss():
    """Redirect must include iss= equal to the AS's issuer URL (RFC 9207)."""
    req = _FakeRequest(_VALID_PARAMS)
    resp = await mcp_server.authorize(req)

    assert resp.status_code == 302
    location = resp.headers["location"]
    assert "iss=" in location, f"iss missing from redirect: {location}"
    assert "https://mcp.concerto.run" in location, f"wrong issuer in: {location}"


@pytest.mark.asyncio
async def test_authorize_redirect_contains_code():
    req = _FakeRequest(_VALID_PARAMS)
    resp = await mcp_server.authorize(req)

    location = resp.headers["location"]
    assert "code=" in location


@pytest.mark.asyncio
async def test_authorize_redirect_contains_state_when_provided():
    req = _FakeRequest(_VALID_PARAMS)
    resp = await mcp_server.authorize(req)

    location = resp.headers["location"]
    assert "state=random-state-xyz" in location


@pytest.mark.asyncio
async def test_authorize_iss_matches_request_host():
    """iss value must reflect the actual server host (not a hardcoded constant)."""
    params = dict(_VALID_PARAMS)
    params["state"] = "s"
    req = _FakeRequest(params, host="custom-host.example.com", proto="https")
    resp = await mcp_server.authorize(req)

    location = resp.headers["location"]
    assert "iss=https://custom-host.example.com" in location


# ── Missing params → 400 ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authorize_missing_client_id_returns_400():
    params = {k: v for k, v in _VALID_PARAMS.items() if k != "client_id"}
    req = _FakeRequest(params)
    resp = await mcp_server.authorize(req)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_authorize_wrong_response_type_returns_400():
    params = dict(_VALID_PARAMS, response_type="token")
    req = _FakeRequest(params)
    resp = await mcp_server.authorize(req)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_authorize_no_state_still_includes_iss():
    """iss must be present even when the client omits state."""
    params = {k: v for k, v in _VALID_PARAMS.items() if k != "state"}
    req = _FakeRequest(params)
    resp = await mcp_server.authorize(req)

    assert resp.status_code == 302
    location = resp.headers["location"]
    assert "iss=" in location
    assert "state=" not in location
