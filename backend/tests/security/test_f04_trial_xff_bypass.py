"""F-04 — Trial IP rate-limit must not trust client-supplied X-Forwarded-For.

A naive `request.headers.get("x-forwarded-for")` lets the attacker spoof
the per-IP rate-limit check by sending a different forged value on each
trial-start.  After hardening we key on `cf-connecting-ip` first, then
fall back to the L4 peer (`request.client.host`).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    from concerto.trial_router import router as trial_router
    app = FastAPI()
    app.include_router(trial_router)
    return app


def _client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


def test_f04_trial_uses_cf_connecting_ip_when_present(monkeypatch):
    """When cf-connecting-ip is set (real prod), it must be the source of
    truth — the attacker's X-Forwarded-For is ignored."""
    captured_ips = []

    async def fake_ip_recent(ip: str) -> bool:
        captured_ips.append(ip)
        return False

    async def fake_email_used(_email: str) -> bool:
        return False

    async def fake_insert(*_a, **_kw):
        return None

    with (
        patch("concerto.trial_router._email_already_trialed", AsyncMock(side_effect=fake_email_used)),
        patch("concerto.trial_router._ip_trialed_recently", AsyncMock(side_effect=fake_ip_recent)),
        patch("concerto.trial_router._insert_trial_buyer", AsyncMock(side_effect=fake_insert)),
        patch("concerto.trial_router.asyncio.create_task"),
    ):
        client = _client()
        r = client.post(
            "/api/trial/start",
            json={"email": "x@example.com"},
            headers={
                "cf-connecting-ip": "203.0.113.7",       # real client (CF-set)
                "x-forwarded-for": "1.1.1.1, 2.2.2.2",   # attacker-supplied
            },
        )
    assert r.status_code in (201, 409, 429)
    # The IP we keyed the rate-limit on must be the cf-connecting-ip,
    # not the attacker's X-Forwarded-For.
    assert captured_ips and captured_ips[0] == "203.0.113.7", (
        f"trial keyed rate-limit on attacker XFF: {captured_ips!r}"
    )


def test_f04_xff_alone_is_not_trusted(monkeypatch):
    """Without cf-connecting-ip, only the L4 peer matters — XFF is ignored."""
    captured_ips = []

    async def fake_ip_recent(ip: str) -> bool:
        captured_ips.append(ip)
        return False

    with (
        patch("concerto.trial_router._email_already_trialed", AsyncMock(return_value=False)),
        patch("concerto.trial_router._ip_trialed_recently", AsyncMock(side_effect=fake_ip_recent)),
        patch("concerto.trial_router._insert_trial_buyer", AsyncMock()),
        patch("concerto.trial_router.asyncio.create_task"),
    ):
        client = _client()
        r = client.post(
            "/api/trial/start",
            json={"email": "y@example.com"},
            headers={"x-forwarded-for": "99.99.99.99"},  # attacker-supplied only
        )
    assert r.status_code in (201, 409, 429)
    assert captured_ips and captured_ips[0] != "99.99.99.99", (
        f"trial trusted attacker-supplied XFF (no CF header present): {captured_ips!r}"
    )
