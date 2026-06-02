"""F-11 — /api/cancel-by-email must rate-limit per real client IP, not per
Cloudflare edge IP.

`request.client.host` behind Cloudflare is a Cloudflare edge IP, so the
existing rate window collapses to "one bucket per CF edge" — many real
buyers share the same bucket, so one noisy CF edge DoSes legitimate
cancellation attempts.

Hardened contract:

  * Use the `cf-connecting-ip` header when present (Cloudflare sets and
    overwrites this; the customer cannot forge it through the CF
    front-door).
  * Fall back to `request.client.host` only when the header is absent
    (direct hits to the backend, dev, tests).
  * Two requests with the same client.host but different
    `cf-connecting-ip` values therefore live in independent quota
    buckets.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client():
    from concerto.customer_portal import router, _CANCEL_ATTEMPTS, _CANCEL_RATE_MAX
    # Wipe the in-memory bucket so each test starts clean.
    _CANCEL_ATTEMPTS.clear()
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False), _CANCEL_RATE_MAX


def test_f11_cf_connecting_ip_is_keyed_separately():
    """Two different real users behind the same CF edge must not share quota."""
    client, max_attempts = _client()

    with patch("concerto.customer_portal.db.get_buyer_by_email",
               AsyncMock(return_value=None)):
        # User A burns through their full quota.
        for _ in range(max_attempts):
            r = client.post(
                "/api/cancel-by-email",
                json={"email": "a@example.com"},
                headers={"cf-connecting-ip": "1.1.1.1"},
            )
            assert r.status_code == 200
            assert r.json()["ok"] is True

        # One more from User A — must be rate-limited (still 200 per
        # anti-enumeration design, but `ok` flips to False on the *honest*
        # signal we keep in the in-memory bucket).  We assert that the
        # bucket for 1.1.1.1 is at the cap.
        from concerto.customer_portal import _CANCEL_ATTEMPTS
        assert len(_CANCEL_ATTEMPTS.get("1.1.1.1", [])) >= max_attempts

        # User B from a different real IP (same CF edge would be identical
        # client.host in prod) must still have an empty bucket.
        r = client.post(
            "/api/cancel-by-email",
            json={"email": "b@example.com"},
            headers={"cf-connecting-ip": "2.2.2.2"},
        )
        assert r.status_code == 200
        # User B's bucket exists, with exactly 1 entry — they were not
        # rate-limited by User A's traffic.
        assert len(_CANCEL_ATTEMPTS.get("2.2.2.2", [])) == 1, (
            "F-11: cancel-by-email keyed buckets by request.client.host "
            "(shared CF edge IP) — User B inherited User A's quota.  "
            f"buckets={dict(_CANCEL_ATTEMPTS)}"
        )


def test_f11_falls_back_to_client_host_without_cf_header():
    """No cf-connecting-ip → fall back to request.client.host."""
    client, _max = _client()

    with patch("concerto.customer_portal.db.get_buyer_by_email",
               AsyncMock(return_value=None)):
        r = client.post("/api/cancel-by-email", json={"email": "x@example.com"})
        assert r.status_code == 200

        from concerto.customer_portal import _CANCEL_ATTEMPTS
        # The TestClient sets request.client.host to "testclient".
        assert "testclient" in _CANCEL_ATTEMPTS
        assert len(_CANCEL_ATTEMPTS["testclient"]) == 1
