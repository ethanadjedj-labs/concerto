"""F-05 — /api/trial/eligibility must not be a free email-enumeration probe.

The old contract returned `{eligible: false, reason: "email_used"}` for
any email that had ever opened a trial.  After hardening, the response
must be uniform regardless of whether the queried email is on record.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client():
    from concerto.trial_router import router
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_f05_eligibility_does_not_leak_email_used():
    """Two equivalent queries — one for an unknown email, one for a known
    email — must return responses with no observable difference that
    encodes 'email has been used'."""
    client = _client()

    # unknown email
    with (
        patch("concerto.trial_router._email_already_trialed", AsyncMock(return_value=False)),
        patch("concerto.trial_router._ip_trialed_recently", AsyncMock(return_value=False)),
    ):
        r_unknown = client.get("/api/trial/eligibility?email=unknown@example.com")

    # known email (would say `email_used` on the old contract)
    with (
        patch("concerto.trial_router._email_already_trialed", AsyncMock(return_value=True)),
        patch("concerto.trial_router._ip_trialed_recently", AsyncMock(return_value=False)),
    ):
        r_known = client.get("/api/trial/eligibility?email=known@example.com")

    assert r_unknown.status_code == r_known.status_code

    j_unknown = r_unknown.json()
    j_known = r_known.json()

    # The two responses must not encode the existence of the email in any
    # field a probing client could read.
    assert j_unknown == j_known, (
        f"eligibility responses differ between unknown vs known email: "
        f"unknown={j_unknown!r} known={j_known!r}"
    )
