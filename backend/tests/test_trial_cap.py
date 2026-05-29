"""Regression tests for trial duration logic in trial_router.

Known fragile paths:
  - Operator emails bypass rate limits and get at least _OPERATOR_TRIAL_DURATION_S
  - Public 30min / 48h plans are honored exactly — no silent cap
  - Unknown plan keys fall back to 30min (not an error, not silently extended)
  - A customer cannot request an arbitrarily long trial via the plan field
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import concerto.trial_router as tr
from concerto.trial_router import router

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app, raise_server_exceptions=True)

_OPERATOR_EMAIL = "adjedjethan@gmail.com"
_PUBLIC_EMAIL = "buyer@example.com"


def _patch_all(monkeypatch):
    """Silence every external call made inside trial_start."""
    monkeypatch.setattr(tr, "_email_already_trialed", AsyncMock(return_value=False))
    monkeypatch.setattr(tr, "_ip_trialed_recently", AsyncMock(return_value=False))
    monkeypatch.setattr(tr, "_insert_trial_buyer", AsyncMock())
    monkeypatch.setattr(tr, "_provision_trial", AsyncMock())


def _start(monkeypatch, email: str, plan: str = "30min") -> dict:
    _patch_all(monkeypatch)
    r = _client.post("/api/trial/start", json={"email": email, "plan": plan})
    assert r.status_code == 201, r.text
    return r.json()


# ── Public trial durations ─────────────────────────────────────────────────────


def test_public_30min_trial_duration(monkeypatch):
    data = _start(monkeypatch, _PUBLIC_EMAIL, plan="30min")
    assert data["trial_duration_minutes"] == 30


def test_public_48h_trial_duration(monkeypatch):
    """48-hour public trial must be honored — no silent cap to 30min."""
    data = _start(monkeypatch, _PUBLIC_EMAIL, plan="48h")
    assert data["trial_duration_minutes"] == 48 * 60


def test_unknown_plan_falls_back_to_30min(monkeypatch):
    """Unknown plan key → default 30min, not an error."""
    data = _start(monkeypatch, _PUBLIC_EMAIL, plan="99years")
    assert data["trial_duration_minutes"] == 30


# ── Operator email bypass ──────────────────────────────────────────────────────


def test_operator_email_gets_extended_duration(monkeypatch):
    """Operator email requesting 30min must receive the operator floor (2h)."""
    data = _start(monkeypatch, _OPERATOR_EMAIL, plan="30min")
    # Operator minimum is 7200s = 120 minutes
    assert data["trial_duration_minutes"] == 120


def test_operator_email_48h_honored(monkeypatch):
    """Operator requesting 48h: 48h > 2h, so 48h wins (max, not cap)."""
    data = _start(monkeypatch, _OPERATOR_EMAIL, plan="48h")
    assert data["trial_duration_minutes"] == 48 * 60


def test_operator_plus_suffix_bypass(monkeypatch):
    """adjedjethan+test@gmail.com must also bypass rate limits."""
    data = _start(monkeypatch, "adjedjethan+test@gmail.com", plan="30min")
    assert data["trial_duration_minutes"] == 120


# ── Rate limiting (non-operator) ───────────────────────────────────────────────


def test_duplicate_email_returns_409(monkeypatch):
    _patch_all(monkeypatch)
    monkeypatch.setattr(tr, "_email_already_trialed", AsyncMock(return_value=True))
    r = _client.post("/api/trial/start", json={"email": _PUBLIC_EMAIL, "plan": "30min"})
    assert r.status_code == 409


def test_ip_rate_limited_returns_429(monkeypatch):
    _patch_all(monkeypatch)
    monkeypatch.setattr(tr, "_ip_trialed_recently", AsyncMock(return_value=True))
    r = _client.post("/api/trial/start", json={"email": _PUBLIC_EMAIL, "plan": "30min"})
    assert r.status_code == 429


def test_operator_email_bypasses_ip_limit(monkeypatch):
    """Operator must proceed even when their IP has been rate-limited."""
    _patch_all(monkeypatch)
    monkeypatch.setattr(tr, "_ip_trialed_recently", AsyncMock(return_value=True))
    r = _client.post("/api/trial/start", json={"email": _OPERATOR_EMAIL, "plan": "30min"})
    assert r.status_code == 201
