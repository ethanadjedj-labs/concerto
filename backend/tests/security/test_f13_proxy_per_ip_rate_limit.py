"""F-13 — MCP proxy needs a per-IP rate limit and a non-destructive bucket GC.

Two problems with the original `_rate_limit_check`:

  1. Per-token bucket only: an attacker hitting many distinct (unknown)
     buyer tokens from one IP gets a fresh bucket per token, so the
     per-token cap (60/min) does not slow them down at all.  Each request
     still reaches the DB, enabling enumeration and DB-query DoS.

  2. `_rl_buckets.clear()` is invoked when the dict grows past 10000
     entries.  An attacker can fill those 10000 entries in a few seconds
     with unique unknown tokens, forcing a global clear that wipes the
     in-memory rate-limit state of every LEGITIMATE buyer.  Cooperative
     DoS / abuse-quota reset.

Hardening:

  * `_ip_rate_limit_check(client_ip)`: a strict per-IP sliding window cap
    on top of the per-token one.  Keyed off `cf-connecting-ip` (with
    `request.client.host` fallback — same pattern as F-04 / F-11).
  * `_gc_rl_buckets()`: evict the oldest-by-activity entries instead of
    blowing away the whole dict, so legitimate buyers' rate-limit state
    survives an attacker-driven token-fuzz storm.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


_BUYER = {
    "token": "tok-legit",
    "vps_id": "concerto-abc",
    "vps_ip": "https://p01--concerto-abc--ns.code.run",
    "mcp_url": "https://p01--concerto-abc--ns.code.run/mcp",
    "bearer_token": "b",
    "status": "active",
    "plan": "solo",
    "runtime_state": None,
    "last_active_at": None,
}


def _app() -> FastAPI:
    from concerto.mcp_proxy_router import router as proxy_router
    app = FastAPI()
    app.include_router(proxy_router)
    return app


def _client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


def _reset_state(proxy_mod):
    proxy_mod._rl_buckets.clear()
    proxy_mod._rl_unknown_per_ip.clear()


def test_f13_per_ip_unknown_token_flood_is_rate_limited():
    """A single CF-IP cannot enumerate >N unknown buyer tokens per minute.

    Today (pre-fix) every distinct token gets its own per-token bucket and
    the same IP can probe arbitrarily many unknown tokens.  Post-fix the
    per-IP cap kicks in well before the attacker can do 100 distinct
    probes.
    """
    import concerto.mcp_proxy_router as proxy_mod
    _reset_state(proxy_mod)

    # Unknown tokens → get_buyer returns None for everything
    with patch("concerto.db.get_buyer", AsyncMock(return_value=None)):
        c = _client()
        codes = []
        for i in range(100):
            r = c.get(
                f"/mcp-proxy/unknown-tok-{i:03d}/mcp",
                headers={"cf-connecting-ip": "203.0.113.7"},
            )
            codes.append(r.status_code)

    # At least one 429 must appear well before the 100th request — the
    # per-IP unknown-token cap must engage.
    assert 429 in codes, (
        "100 unknown-token probes from one IP all succeeded — no per-IP rate limit"
    )
    first_429 = codes.index(429)
    assert first_429 < 50, (
        f"Per-IP cap engaged too late at request #{first_429}; "
        "attacker can still cheaply enumerate"
    )


def test_f13_bucket_gc_preserves_legitimate_buyer_state():
    """`_rl_buckets` GC must NOT blow away legit buyers' rate-limit history.

    An attacker filling _rl_buckets with 10001 unknown-token entries would
    formerly trigger `_rl_buckets.clear()`, wiping every legit buyer's
    rate-limit state.  Post-fix: legit buyer's bucket must survive.
    """
    import concerto.mcp_proxy_router as proxy_mod
    _reset_state(proxy_mod)

    # Pre-populate a legitimate buyer's bucket near its limit.
    import time as _t
    now = _t.monotonic()
    proxy_mod._rl_buckets["tok-legit"] = [now - 1.0] * 50  # 50 recent requests

    # Now simulate attacker fuzz: 11000 distinct unknown tokens enter the
    # buckets dict.  We bypass _ip_rate_limit by calling the GC path
    # directly.  (We don't want the per-IP cap to short-circuit our flood,
    # since the point of this test is the GC behaviour.)
    for i in range(11000):
        proxy_mod._rl_buckets[f"fuzz-{i:05d}"] = [now - 2.0]
    proxy_mod._gc_rl_buckets()

    # The legitimate buyer's bucket must still exist after GC.
    assert "tok-legit" in proxy_mod._rl_buckets, (
        "GC wiped legitimate buyer's rate-limit state — cooperative DoS"
    )
    assert len(proxy_mod._rl_buckets["tok-legit"]) >= 50, (
        "Legitimate buyer's per-token request history was reset by GC"
    )
    # And the dict has actually shrunk (GC did something).
    assert len(proxy_mod._rl_buckets) < 11001, "GC did not evict any entries"


def test_f13_per_ip_cap_does_not_block_one_legit_buyer():
    """A single legitimate buyer hitting their own token must NOT trip the
    per-IP cap before the per-token cap.

    The per-IP cap is sized so that one buyer's own ~60/min cap is the
    binding constraint — not the per-IP cap.  This guards against a
    too-tight per-IP cap killing real users.
    """
    import concerto.mcp_proxy_router as proxy_mod
    _reset_state(proxy_mod)

    upstream = MagicMock()
    upstream.status_code = 200
    upstream.headers = {"content-type": "application/json"}

    async def _aiter(chunk_size=4096):
        yield b'{"ok":true}'

    upstream.aiter_bytes = _aiter
    upstream.aclose = AsyncMock()

    client = MagicMock()
    client.build_request = MagicMock(return_value=MagicMock())
    client.send = AsyncMock(return_value=upstream)
    client.aclose = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("concerto.db.get_buyer", AsyncMock(return_value=_BUYER)),
        patch("concerto.db.update_buyer", AsyncMock()),
        patch.object(proxy_mod.httpx, "AsyncClient", return_value=client),
    ):
        c = _client()
        codes = []
        for _ in range(40):  # well within per-token cap (60/min)
            r = c.post(
                "/mcp-proxy/tok-legit/mcp",
                json={"method": "tools/list"},
                headers={"cf-connecting-ip": "198.51.100.42"},
            )
            codes.append(r.status_code)

    # All should succeed: per-token cap is 60/min, we sent 40.
    assert all(code == 200 for code in codes), (
        f"Legit buyer was rate-limited at request "
        f"#{codes.index(next(c for c in codes if c != 200))}: {codes}"
    )
