"""F-02 — /api/internal/droplet-ready must fail CLOSED when no callback
secret is stored.

The current code only enforces `hmac.compare_digest` when the buyer row
already has a non-empty `callback_secret` or `ttyd_password`.  During the
brief install window before either is written, the endpoint accepts
arbitrary mcp_url / bearer_token from any caller who knows the buyer
token — letting an attacker pin the per-buyer MCP proxy to a host they
control.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    from concerto.provision_router import router as prov_router
    app = FastAPI()
    app.include_router(prov_router)
    return app


def _client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


def _buyer(callback_secret=None, ttyd_password=None, status="installing"):
    return {
        "token": "tok-install-window",
        "callback_secret": callback_secret,
        "ttyd_password": ttyd_password,
        "status": status,
        "vps_ip": None,
        "plan": "solo",
        "email": "buyer@example.com",
    }


def test_f02_no_stored_secret_rejects_callback():
    """During the install window both secret fields are empty/None.
    The callback MUST be rejected (fail-closed)."""
    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=_buyer())),
        patch("concerto.db.update_buyer", AsyncMock()) as update,
    ):
        client = _client()
        r = client.post(
            "/api/internal/droplet-ready",
            headers={"X-Callback-Secret": "anything-attacker-supplies"},
            json={
                "token": "tok-install-window",
                "mcp_url": "https://attacker.example/mcp",
                "bearer_token": "attacker-bearer",
                "ttyd_url": "https://attacker.example/ttyd",
            },
        )

    assert r.status_code in (401, 403, 503), (
        f"expected fail-closed status, got {r.status_code} body={r.text!r}"
    )
    # Crucial: NO mcp_url update was committed.
    for call in update.call_args_list:
        _args, kwargs = call
        assert "mcp_url" not in kwargs or kwargs["mcp_url"] != "https://attacker.example/mcp", (
            "attacker's mcp_url was written despite missing callback secret"
        )


def test_f02_empty_string_stored_secret_also_rejects():
    """Empty string is the equivalent of None and must fail-closed too."""
    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=_buyer(callback_secret="", ttyd_password=""))),
        patch("concerto.db.update_buyer", AsyncMock()) as update,
    ):
        client = _client()
        r = client.post(
            "/api/internal/droplet-ready",
            headers={"X-Callback-Secret": "anything"},
            json={
                "token": "tok-install-window",
                "mcp_url": "https://attacker.example/mcp",
                "bearer_token": "attacker-bearer",
            },
        )

    assert r.status_code in (401, 403, 503), (
        f"expected fail-closed status, got {r.status_code} body={r.text!r}"
    )
    for call in update.call_args_list:
        _args, kwargs = call
        assert "mcp_url" not in kwargs or kwargs["mcp_url"] != "https://attacker.example/mcp"


def test_f02_correct_callback_secret_still_accepted():
    """The legitimate provisioner path (callback_secret WAS written before
    the droplet booted) continues to work — no regression."""
    b = _buyer(callback_secret="legit-secret-xyz")
    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=b)),
        patch("concerto.db.update_buyer", AsyncMock()),
    ):
        client = _client()
        r = client.post(
            "/api/internal/droplet-ready",
            headers={"X-Callback-Secret": "legit-secret-xyz"},
            json={
                "token": "tok-install-window",
                "mcp_url": "https://nf-real.example/mcp",
                "bearer_token": "legit-bearer",
            },
        )
    assert r.status_code == 200, f"legit callback was rejected: {r.text!r}"


def test_f02_wrong_secret_rejected_when_stored():
    """Negative regression: wrong secret is still rejected."""
    b = _buyer(callback_secret="legit-secret-xyz")
    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=b)),
        patch("concerto.db.update_buyer", AsyncMock()),
    ):
        client = _client()
        r = client.post(
            "/api/internal/droplet-ready",
            headers={"X-Callback-Secret": "wrong"},
            json={
                "token": "tok-install-window",
                "mcp_url": "https://x.example/mcp",
                "bearer_token": "b",
            },
        )
    assert r.status_code == 403
