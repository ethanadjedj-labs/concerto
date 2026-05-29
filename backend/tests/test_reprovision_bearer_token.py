"""Regression tests for the /api/internal/droplet-ready endpoint.

Known fragile paths:
  - Re-provision must refresh bearer_token in DB so /mcp proxy calls don't 401
    on the stale token (bug fixed: droplet-ready skipped bearer_token on
    already-active buyers)
  - Callback secret validation must reject wrong secrets with 403
  - Fresh provision (status=installing) sets status to awaiting_oauth
"""
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import concerto.provision_router as pr
from concerto.provision_router import router

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app, raise_server_exceptions=True)

_SECRET = "cbk-secret-xyz"


def _past_installing_buyer(token: str = "tok-reprov") -> dict:
    return {
        "token": token,
        "status": "awaiting_oauth",
        "callback_secret": _SECRET,
        "ttyd_password": _SECRET,
        "email": "test@example.com",
        "plan": "solo",
        "mcp_url": "https://old.mcp.example.com/mcp",
        "bearer_token": "stale-bearer-old",
    }


def _patch_db(monkeypatch, buyer: dict) -> dict:
    """Monkeypatch db.get_buyer and db.update_buyer; return captured kwargs."""
    updates: dict = {}

    async def fake_get(tok):
        return buyer

    async def fake_update(tok, **kwargs):
        updates.update(kwargs)

    monkeypatch.setattr(pr.db, "get_buyer", fake_get)
    monkeypatch.setattr(pr.db, "update_buyer", fake_update)
    return updates


# ── Re-provision: bearer_token must be updated ────────────────────────────────


def test_reprovision_updates_bearer_token(monkeypatch):
    """Re-provision callback with new bearer → bearer_token written to DB."""
    buyer = _past_installing_buyer()
    updates = _patch_db(monkeypatch, buyer)

    r = _client.post(
        "/api/internal/droplet-ready",
        json={
            "token": buyer["token"],
            "mcp_url": "https://new.mcp.example.com/mcp",
            "bearer_token": "brand-new-bearer",
        },
        headers={"X-Callback-Secret": _SECRET},
    )
    assert r.status_code == 200
    assert r.json().get("mcp_url_refreshed") is True
    assert "bearer_token" in updates, "bearer_token must be persisted on re-provision"
    assert updates["bearer_token"] == "brand-new-bearer"


def test_reprovision_updates_mcp_url(monkeypatch):
    """New mcp_url must always be persisted on re-provision."""
    buyer = _past_installing_buyer()
    updates = _patch_db(monkeypatch, buyer)

    r = _client.post(
        "/api/internal/droplet-ready",
        json={
            "token": buyer["token"],
            "mcp_url": "https://new.mcp.example.com/mcp",
            "bearer_token": "new-bearer",
        },
        headers={"X-Callback-Secret": _SECRET},
    )
    assert r.status_code == 200
    assert updates.get("mcp_url") == "https://new.mcp.example.com/mcp"


def test_reprovision_no_bearer_payload_skips_bearer_update(monkeypatch):
    """Empty bearer in payload (steady-state restart) must NOT overwrite bearer."""
    buyer = _past_installing_buyer()
    updates = _patch_db(monkeypatch, buyer)

    r = _client.post(
        "/api/internal/droplet-ready",
        json={
            "token": buyer["token"],
            "mcp_url": "https://same.mcp.example.com/mcp",
            "bearer_token": "",  # container sent blank (steady-state restart)
        },
        headers={"X-Callback-Secret": _SECRET},
    )
    assert r.status_code == 200
    assert "bearer_token" not in updates, "blank bearer must not overwrite stored token"


# ── Callback secret validation ────────────────────────────────────────────────


def test_wrong_callback_secret_returns_403(monkeypatch):
    buyer = _past_installing_buyer()
    _patch_db(monkeypatch, buyer)

    r = _client.post(
        "/api/internal/droplet-ready",
        json={
            "token": buyer["token"],
            "mcp_url": "https://new.mcp.example.com/mcp",
            "bearer_token": "new-bearer",
        },
        headers={"X-Callback-Secret": "wrong-secret"},
    )
    assert r.status_code == 403


def test_missing_token_returns_404(monkeypatch):
    monkeypatch.setattr(pr.db, "get_buyer", AsyncMock(return_value=None))
    r = _client.post(
        "/api/internal/droplet-ready",
        json={"token": "nonexistent", "mcp_url": "https://x.example.com/mcp", "bearer_token": "x"},
        headers={"X-Callback-Secret": _SECRET},
    )
    assert r.status_code == 404


# ── Fresh provision: installing → awaiting_oauth ──────────────────────────────


def test_fresh_provision_sets_awaiting_oauth(monkeypatch):
    """First-time droplet-ready call (status=installing) must set awaiting_oauth."""
    buyer = {
        "token": "tok-fresh",
        "status": "installing",
        "callback_secret": _SECRET,
        "ttyd_password": _SECRET,
        "email": "fresh@example.com",
        "plan": "byoc",
    }
    updates: dict = {}

    async def fake_get(tok):
        return buyer

    async def fake_update(tok, **kwargs):
        updates.update(kwargs)

    monkeypatch.setattr(pr.db, "get_buyer", fake_get)
    monkeypatch.setattr(pr.db, "update_buyer", fake_update)

    r = _client.post(
        "/api/internal/droplet-ready",
        json={
            "token": "tok-fresh",
            "mcp_url": "https://fresh.mcp.example.com/mcp",
            "bearer_token": "fresh-bearer",
        },
        headers={"X-Callback-Secret": _SECRET},
    )
    assert r.status_code == 200
    assert updates.get("status") == "awaiting_oauth"
    assert updates.get("bearer_token") == "fresh-bearer"
    assert updates.get("mcp_url") == "https://fresh.mcp.example.com/mcp"
