"""Unit tests for concerto.cf_tunnel.

Covers:
  - _derive_label: deterministic, DNS-valid, collision-resistant
  - create_named_tunnel: success (201), idempotent 409 path, hostname collision
  - destroy_named_tunnel: success, missing env vars, 404 graceful, DNS sweep
"""
from __future__ import annotations

import asyncio
import hashlib
import os
from unittest.mock import AsyncMock, MagicMock, patch


def _resp(status: int, json_data: dict | None = None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data or {}
    r.text = text
    r.raise_for_status = MagicMock()
    return r


class _AsyncClient:
    """Minimal async-context-manager httpx client mock."""
    def __init__(self):
        self._get_responses: list = []
        self._post_responses: list = []
        self._put_responses: list = []
        self._delete_responses: list = []
        self.get_calls: list = []
        self.post_calls: list = []
        self.delete_calls: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def _next(self, store: list, url: str):
        if not store:
            raise AssertionError(f"No more mocked responses for {url!r}")
        return store.pop(0)

    async def get(self, url, **kw):
        self.get_calls.append(url)
        return self._next(self._get_responses, url)

    async def post(self, url, **kw):
        self.post_calls.append(url)
        return self._next(self._post_responses, url)

    async def put(self, url, **kw):
        return self._next(self._put_responses, url)

    async def delete(self, url, **kw):
        self.delete_calls.append(url)
        return self._next(self._delete_responses, url)


_ENV = {
    "CLOUDFLARE_API_TOKEN": "cf-test-token",
    "CLOUDFLARE_ACCOUNT_ID": "acct-test-123",
}


# ── _derive_label ─────────────────────────────────────────────────────────────

class TestDeriveLabel:
    def test_starts_with_c(self):
        from concerto.cf_tunnel import _derive_label
        assert _derive_label("any-token").startswith("c")

    def test_length_is_17(self):
        from concerto.cf_tunnel import _derive_label
        assert len(_derive_label("any-token")) == 17

    def test_only_lowercase_alphanum(self):
        from concerto.cf_tunnel import _derive_label
        label = _derive_label("some-random-token-value")
        assert label.isalnum() and label == label.lower()

    def test_deterministic_same_input(self):
        from concerto.cf_tunnel import _derive_label
        assert _derive_label("tok123") == _derive_label("tok123")

    def test_different_tokens_produce_different_labels(self):
        from concerto.cf_tunnel import _derive_label
        assert _derive_label("token-a") != _derive_label("token-b")

    def test_matches_sha256_formula(self):
        from concerto.cf_tunnel import _derive_label
        expected = "c" + hashlib.sha256(b"mytoken").hexdigest()[:16]
        assert _derive_label("mytoken") == expected


# ── create_named_tunnel: success (201) ────────────────────────────────────────

class TestCreateNamedTunnelSuccess:
    def test_new_tunnel_created_and_dns_record_added(self):
        from concerto.cf_tunnel import create_named_tunnel, _derive_label
        token = "test-customer-token"
        label = _derive_label(token)
        tunnel_id = "tun-aaa-bbb"
        tunnel_token = "eyJtest"

        client = _AsyncClient()
        # POST /cfd_tunnel → 201 created
        client._post_responses = [
            _resp(201, {"result": {"id": tunnel_id, "token": tunnel_token}}),
            _resp(201, {}),  # POST DNS record
        ]
        # PUT /configurations → 200
        client._put_responses = [_resp(200, {})]
        # GET DNS check → no existing record
        client._get_responses = [
            _resp(200, {"result": []}),
        ]

        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            result = asyncio.run(create_named_tunnel(token))

        assert result["tunnel_id"] == tunnel_id
        assert result["tunnel_token"] == tunnel_token
        assert result["hostname"] == f"{label}.concerto.run"

    def test_existing_cname_for_same_tunnel_not_duplicated(self):
        from concerto.cf_tunnel import create_named_tunnel, _derive_label
        token = "reuse-token"
        tunnel_id = "tun-reuse"
        label = _derive_label(token)
        expected_cname = f"{tunnel_id}.cfargotunnel.com"

        client = _AsyncClient()
        client._post_responses = [
            _resp(201, {"result": {"id": tunnel_id, "token": "tok-reuse"}}),
        ]
        client._put_responses = [_resp(200, {})]
        # DNS record already points to THIS tunnel — idempotent
        client._get_responses = [
            _resp(200, {"result": [{"content": expected_cname, "id": "rec-1"}]}),
        ]

        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            result = asyncio.run(create_named_tunnel(token))

        # No second POST for DNS record — get_calls should have 1 entry only
        assert result["tunnel_id"] == tunnel_id
        assert len(client.post_calls) == 1  # only the tunnel creation


# ── create_named_tunnel: idempotent 409 path ─────────────────────────────────

class TestCreateNamedTunnelIdempotent409:
    def test_409_looks_up_existing_tunnel(self):
        from concerto.cf_tunnel import create_named_tunnel, _derive_label
        token = "existing-token"
        existing_id = "tun-existing"
        existing_tok = "eyJexisting"
        label = _derive_label(token)

        client = _AsyncClient()
        # POST /cfd_tunnel → 409 conflict
        client._post_responses = [
            _resp(409, {}, "tunnel name already in use"),
            _resp(201, {}),  # POST DNS record
        ]
        # GET list tunnels (lookup by name) → returns existing tunnel
        # GET tunnel token
        # GET DNS check → no record
        client._get_responses = [
            _resp(200, {"result": [{"id": existing_id}]}),
            _resp(200, {"result": existing_tok}),
            _resp(200, {"result": []}),
        ]
        client._put_responses = [_resp(200, {})]

        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            result = asyncio.run(create_named_tunnel(token))

        assert result["tunnel_id"] == existing_id
        assert result["tunnel_token"] == existing_tok
        assert result["hostname"] == f"{label}.concerto.run"


# ── create_named_tunnel: collision ───────────────────────────────────────────

class TestCreateNamedTunnelCollision:
    def test_cname_pointing_to_different_tunnel_raises(self):
        import pytest
        from concerto.cf_tunnel import create_named_tunnel
        token = "collision-token"
        our_tunnel_id = "tun-ours"

        client = _AsyncClient()
        client._post_responses = [
            _resp(201, {"result": {"id": our_tunnel_id, "token": "tok-ours"}}),
        ]
        client._put_responses = [_resp(200, {})]
        # DNS record points to a DIFFERENT tunnel
        client._get_responses = [
            _resp(200, {"result": [{"content": "tun-theirs.cfargotunnel.com"}]}),
        ]

        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            with pytest.raises(RuntimeError, match="collision"):
                asyncio.run(create_named_tunnel(token))


# ── destroy_named_tunnel ──────────────────────────────────────────────────────

class TestDestroyNamedTunnel:
    def test_empty_tunnel_id_is_noop(self):
        from concerto.cf_tunnel import destroy_named_tunnel
        client = _AsyncClient()
        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            asyncio.run(destroy_named_tunnel(""))
        assert client.delete_calls == []

    def test_missing_env_vars_logs_and_returns(self):
        from concerto.cf_tunnel import destroy_named_tunnel
        client = _AsyncClient()
        with (
            patch("httpx.AsyncClient", return_value=client),
            patch.dict(os.environ, {}, clear=True),
        ):
            asyncio.run(destroy_named_tunnel("tun-abc"))
        assert client.delete_calls == []

    def test_successful_delete_tunnel_and_dns(self):
        from concerto.cf_tunnel import destroy_named_tunnel
        client = _AsyncClient()
        client._delete_responses = [
            _resp(200, {}),  # DELETE tunnel
            _resp(200, {}),  # DELETE DNS record
        ]
        # GET DNS records matching this tunnel
        client._get_responses = [
            _resp(200, {"result": [{"id": "dns-rec-1"}]}),
        ]
        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            asyncio.run(destroy_named_tunnel("tun-xyz"))

        assert any("tun-xyz" in url for url in client.delete_calls)

    def test_404_on_delete_is_graceful(self):
        from concerto.cf_tunnel import destroy_named_tunnel
        client = _AsyncClient()
        client._delete_responses = [
            _resp(404, {}),  # tunnel already gone
        ]
        client._get_responses = [
            _resp(200, {"result": []}),  # no DNS records to sweep
        ]
        with patch("httpx.AsyncClient", return_value=client), patch.dict(os.environ, _ENV):
            asyncio.run(destroy_named_tunnel("tun-gone"))  # must not raise
