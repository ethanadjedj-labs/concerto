"""F-01 — GitHub-OAuth state must not be the raw buyer token.

If the `state` parameter is the buyer token, an attacker who initiates the
flow with `state = <their_own_token>` can trick the victim into completing
the GitHub consent — and the victim's GitHub access_token gets persisted on
the attacker's buyer row (which the attacker can then read via
`/git-credentials` using their own callback_secret).

These tests:

  1. Connect endpoint must NOT emit `state = <token>`; the redirect URL's
     state must be opaque and non-equal to the buyer token.
  2. Callback endpoint must REJECT a callback whose `state` is just the
     buyer token (no signature envelope).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    from concerto.github_router import router as gh_router
    app = FastAPI()
    app.include_router(gh_router)
    return app


def _client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


_FAKE_BUYER = {
    "token": "tok-buyer-abc",
    "email": "victim@example.com",
    "ttyd_password": "pw-abc",
    "callback_secret": "cb-abc",
    "github_token": None,
    "status": "active",
}


def test_f01_connect_redirect_state_is_not_raw_buyer_token():
    """Regression: /connect must not send `state=<token>` to GitHub."""
    with (
        patch("concerto.github_router._GITHUB_CLIENT_ID", "cid"),
        patch("concerto.github_router._GITHUB_CLIENT_SECRET", "csec"),
        patch("concerto.db.get_buyer", AsyncMock(return_value=_FAKE_BUYER)),
    ):
        client = _client()
        r = client.get(
            "/api/buyer/tok-buyer-abc/github/connect",
            follow_redirects=False,
        )

    assert r.status_code in (302, 303), f"expected redirect, got {r.status_code}"
    location = r.headers.get("location", "")
    qs = parse_qs(urlparse(location).query)
    state = (qs.get("state") or [""])[0]

    # The whole point of F-01: state must NOT be the raw buyer token.
    assert state != "tok-buyer-abc", (
        f"state must not be the raw buyer token; got state={state!r}"
    )
    # And the state still must encode the token somehow (so the callback can
    # look the buyer up after verifying the signature).  We assert it is
    # non-empty as a baseline.
    assert state, "state must be non-empty"


def test_f01_callback_rejects_unsigned_state():
    """Regression: /api/github/callback must reject `state = <token>`.

    The attack reduces to: GitHub posts back `state = tok_victim`.  If the
    handler trusts it and stores the access_token on tok_victim, F-01
    works.  After hardening, an unsigned state must be rejected.
    """
    with (
        patch("concerto.github_router._GITHUB_CLIENT_ID", "cid"),
        patch("concerto.github_router._GITHUB_CLIENT_SECRET", "csec"),
        patch("concerto.db.get_buyer", AsyncMock(return_value=_FAKE_BUYER)),
        patch(
            "concerto.github_router._exchange_and_store",
            AsyncMock(return_value="connected"),
        ) as mock_exchange,
    ):
        client = _client()
        # An attacker hands GitHub a bare buyer token as state.
        r = client.get(
            "/api/github/callback?code=anything&state=tok-buyer-abc",
            follow_redirects=False,
        )

    # We don't care about the status code (popup-close HTML returns 200 with
    # status="error"); what we care about is that no token exchange happened.
    assert not mock_exchange.called, (
        "callback exchanged a GitHub code for an unsigned state — F-01 is live"
    )


def test_f01_callback_accepts_freshly_signed_state():
    """After hardening, the /connect-emitted signed state must round-trip
    cleanly through the callback."""
    import concerto.github_router as gh

    if not hasattr(gh, "_sign_state"):
        # Not yet implemented — this asserts the fix shape.
        import pytest
        pytest.fail("Hardening not yet applied: _sign_state helper missing")

    state = gh._sign_state("tok-buyer-abc")

    with (
        patch("concerto.github_router._GITHUB_CLIENT_ID", "cid"),
        patch("concerto.github_router._GITHUB_CLIENT_SECRET", "csec"),
        patch("concerto.db.get_buyer", AsyncMock(return_value=_FAKE_BUYER)),
        patch(
            "concerto.github_router._exchange_and_store",
            AsyncMock(return_value="connected"),
        ) as mock_exchange,
    ):
        client = _client()
        r = client.get(
            f"/api/github/callback?code=goodcode&state={state}",
            follow_redirects=False,
        )

    assert mock_exchange.called, "signed state was wrongly rejected"
    args, _ = mock_exchange.call_args
    assert args[0] == "tok-buyer-abc"
