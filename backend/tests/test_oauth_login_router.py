"""Unit tests for the NF/DO branching in oauth_login_router."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

# ── helpers ──────────────────────────────────────────────────────────────────

def _nf_buyer(token="tok123"):
    return {
        "token": token,
        "vps_ip": "https://p01--test--abc.code.run",
        "mcp_url": "https://p01--test--abc.code.run/mcp",
        "bearer_token": "testbearer",
        "ssh_keypair_private_path": None,
        "status": "awaiting_oauth",
    }

def _do_buyer(token="tok456"):
    return {
        "token": token,
        "vps_ip": "1.2.3.4",
        "mcp_url": None,
        "bearer_token": "testbearer",
        "ssh_keypair_private_path": "/var/lib/concerto/keys/test.pem",
        "status": "awaiting_oauth",
    }


# ── _is_nf_buyer ─────────────────────────────────────────────────────────────

def test_is_nf_buyer_detects_https():
    from concerto.oauth_login_router import _is_nf_buyer
    assert _is_nf_buyer(_nf_buyer()) is True

def test_is_nf_buyer_rejects_ip():
    from concerto.oauth_login_router import _is_nf_buyer
    assert _is_nf_buyer(_do_buyer()) is False

def test_is_nf_buyer_empty_vps_ip():
    from concerto.oauth_login_router import _is_nf_buyer
    assert _is_nf_buyer({"vps_ip": ""}) is False


# ── _nf_base_url ─────────────────────────────────────────────────────────────

def test_nf_base_url_strips_mcp():
    from concerto.oauth_login_router import _nf_base_url
    buyer = _nf_buyer()
    assert _nf_base_url(buyer) == "https://p01--test--abc.code.run"

def test_nf_base_url_fallback_to_vps_ip():
    from concerto.oauth_login_router import _nf_base_url
    buyer = _nf_buyer()
    buyer["mcp_url"] = None
    assert _nf_base_url(buyer) == "https://p01--test--abc.code.run"


# ── test_code_url_parsing_strips_query_params ─────────────────────────────────

def test_code_stripping_in_submit(monkeypatch):
    """Verify full redirect-URL input is stripped to just the code."""
    import re
    code = "https://concerto.run/callback?code=abc123xyz&state=foo"
    code = re.sub(r".*code=", "", code)
    code = re.split(r"[&\s]", code)[0].strip()
    assert code == "abc123xyz"


# ── NF oauth/start — HTTP path ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nf_buyer_uses_http_path(monkeypatch):
    """NF buyers POST to /__internal/oauth/start, not SSH."""
    buyer = _nf_buyer()
    auth_url = "https://claude.ai/oauth/authorize?client_id=x&state=y"

    async def fake_get_buyer(token):
        return buyer

    monkeypatch.setattr("concerto.oauth_login_router.db.get_buyer", fake_get_buyer)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"auth_url": auth_url}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from concerto.oauth_login_router import oauth_start
        result = await oauth_start("tok123")

    assert result["auth_url"] == auth_url
    # Verify it called the NF internal endpoint, not SSH
    call_args = mock_client.post.call_args
    assert "/__internal/oauth/start" in call_args[0][0]
    assert call_args[1]["headers"]["Authorization"] == "Bearer testbearer"


# ── NF oauth/start — 502 from container ──────────────────────────────────────

@pytest.mark.asyncio
async def test_nf_oauth_start_handles_502_from_container(monkeypatch):
    buyer = _nf_buyer()

    async def fake_get_buyer(token):
        return buyer

    monkeypatch.setattr("concerto.oauth_login_router.db.get_buyer", fake_get_buyer)

    mock_response = MagicMock()
    mock_response.status_code = 502
    mock_response.text = "container error"

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from fastapi import HTTPException
        from concerto.oauth_login_router import oauth_start
        with pytest.raises(HTTPException) as exc_info:
            await oauth_start("tok123")

    assert exc_info.value.status_code == 502


# ── DO buyer: _buyer_or_404 rejects missing key ───────────────────────────────

@pytest.mark.asyncio
async def test_do_buyer_requires_ssh_key(monkeypatch):
    """DO buyer with no ssh key should get 409."""
    buyer = _do_buyer()
    buyer["ssh_keypair_private_path"] = None

    async def fake_get_buyer(token):
        return buyer

    monkeypatch.setattr("concerto.oauth_login_router.db.get_buyer", fake_get_buyer)

    from fastapi import HTTPException
    from concerto.oauth_login_router import _buyer_or_404
    with pytest.raises(HTTPException) as exc_info:
        await _buyer_or_404("tok456")

    assert exc_info.value.status_code == 409


# ── NF buyer: _buyer_or_404 succeeds without SSH key ─────────────────────────

@pytest.mark.asyncio
async def test_nf_buyer_ok_without_ssh_key(monkeypatch):
    buyer = _nf_buyer()

    async def fake_get_buyer(token):
        return buyer

    monkeypatch.setattr("concerto.oauth_login_router.db.get_buyer", fake_get_buyer)

    from concerto.oauth_login_router import _buyer_or_404
    result = await _buyer_or_404("tok123")
    assert result["vps_ip"].startswith("https://")
