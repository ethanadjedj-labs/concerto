"""MCP transparent wake-up proxy.

Route: ANY /mcp-proxy/{buyer_token}/{path:path}

For each incoming MCP request:
  1. Resolve buyer by URL token.  404 if unknown.
  2. If runtime_state == 'paused': call provider.resume(), poll /healthz
     until 200 or 30 s, then clear runtime_state.  504 on timeout.
  3. Forward the full request (method, headers, body, query params) to the
     NF service via httpx streaming.  SSE streams are streamed back without
     buffering.
  4. Update last_active_at on every successful forwarded request.

Internal target URL is derived from buyer.vps_ip (the stable NF URL stored at
provision time, e.g. https://p01--concerto-abc--ns.code.run).  The proxy path
is appended directly: {vps_ip}/{path}.

The customer-visible URL (returned by status_router) is:
  https://api.concerto.run/mcp-proxy/{token}/mcp

The direct NF URL is kept in mcp_url in DB for internal health monitoring;
this proxy does not read mcp_url.
"""
from __future__ import annotations

import asyncio
import logging
import time

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from concerto import db, provider_factory as provisioner

router = APIRouter()
logger = logging.getLogger(__name__)

_WAKE_TIMEOUT_S = 30          # max seconds to wait for /healthz after resume
_POLL_INTERVAL_S = 1.5        # seconds between /healthz polls
_FORWARD_CONNECT_S = 10.0     # httpx connect timeout
_FORWARD_READ_S = 300.0       # httpx read timeout (long for SSE streams)

# Hop-by-hop headers that must not be forwarded.
_HOP_BY_HOP = frozenset([
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
    "host", "content-length",
])


# F-03: defence-in-depth path validation.  Reject anything that:
#   * contains "..", "//" (double-slash anywhere — keeps the upstream URL
#     unambiguous), NUL bytes, CR/LF, or non-printable chars;
#   * URL-decodes into the same set;
#   * looks like a scheme prefix (http:, https:, file:, …) so an attacker
#     cannot try to coerce the forwarder into hitting another host.
# Returns (target_url, error_message). One is None.
def _safe_target_url(vps_ip: str, path: str) -> tuple[str | None, str | None]:
    import urllib.parse as _up

    # Reject pre-decoded literal traversal first.
    raw = path or ""
    if "\x00" in raw or "\r" in raw or "\n" in raw:
        return None, "control_char_in_path"

    # Decode once and re-check (FastAPI's {path:path} already URL-decodes,
    # but we re-quote and recompare to catch double-encoding tricks).
    try:
        decoded = _up.unquote(raw)
    except Exception:
        return None, "undecodable_path"

    forbidden_substrings = ("..", "//", "\x00", "\r", "\n")
    for needle in forbidden_substrings:
        if needle in raw or needle in decoded:
            return None, f"forbidden_substring:{needle!r}"

    # Reject scheme-shaped prefixes anywhere in the first segment.
    low = decoded.lower().lstrip("/")
    for scheme in ("http:", "https:", "ws:", "wss:", "file:", "ftp:", "gopher:"):
        if low.startswith(scheme):
            return None, f"scheme_prefix:{scheme}"

    # The vps_ip we proxy to must be a known-shape https URL.  We do not
    # validate the suffix here (the operator may move providers), but we
    # require https + a host.
    base = (vps_ip or "").rstrip("/")
    parsed = _up.urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc:
        return None, "bad_upstream_base"

    return f"{base}/{raw}", None

# ── Rate-limit (in-memory) ────────────────────────────────────────────────────
# Two sliding-window counters keyed by buyer_token AND by client IP.  The
# per-token cap protects buyers from one another; the per-IP-on-unknown
# cap stops a single attacker IP from cheaply enumerating buyer tokens or
# flooding `_rl_buckets` to force a global GC clear (F-13).
_RL_WINDOW_S = 60          # window length
_RL_MAX_PER_WINDOW = 60    # max requests per buyer per window (1/s avg, bursty)
_RL_BUCKETS_CAP = 10000    # entries before GC kicks in

# Per-IP cap that ONLY counts requests targeting unknown tokens.  A real
# buyer hits a single (known) token from their browser, so they never
# touch this counter.  An attacker fuzzing tokens trips it fast.
_RL_UNKNOWN_WINDOW_S = 60
_RL_UNKNOWN_MAX_PER_IP = 20

_rl_buckets: dict[str, list[float]] = {}
_rl_unknown_per_ip: dict[str, list[float]] = {}


def _gc_rl_buckets() -> None:
    """LRU-style eviction for `_rl_buckets`.

    Pre-F-13 this method was `_rl_buckets.clear()`, which let an attacker
    fill the dict with throwaway tokens and force a wipe of every
    legitimate buyer's rate-limit state.  Now we keep the most-recently-
    active half of the entries — the attacker's stale tokens get dropped
    while legitimate buyers' history survives.
    """
    if len(_rl_buckets) <= _RL_BUCKETS_CAP:
        return
    # Sort by most-recent activity ascending.  Drop the older half.
    items = sorted(
        _rl_buckets.items(),
        key=lambda kv: (kv[1][-1] if kv[1] else 0.0),
    )
    drop_n = len(items) // 2
    for tok, _ in items[:drop_n]:
        _rl_buckets.pop(tok, None)


def _rate_limit_check(buyer_token: str) -> bool:
    """Return True if the request is allowed, False if rate-limited.

    Uses a sliding-window counter per buyer_token.  Tokens are limited
    independently — one abusive client cannot DoS the others.
    """
    import time as _t
    now = _t.monotonic()
    cutoff = now - _RL_WINDOW_S
    bucket = _rl_buckets.get(buyer_token, [])
    # Drop entries older than the window
    bucket = [t for t in bucket if t > cutoff]
    if len(bucket) >= _RL_MAX_PER_WINDOW:
        _rl_buckets[buyer_token] = bucket
        return False
    bucket.append(now)
    _rl_buckets[buyer_token] = bucket
    # GC when full — drops the oldest-by-activity half so legitimate
    # buyers' state survives an attacker-driven fuzz storm (F-13).
    _gc_rl_buckets()
    return True


def _unknown_token_ip_check(client_ip: str) -> bool:
    """F-13: per-IP cap on requests that target UNKNOWN buyer tokens.

    Returns True if the request is still under the cap.  Tracked
    separately from `_rl_buckets` so a legitimate buyer hitting their
    own token from many IPs (e.g. mobile) does not consume budget here.
    """
    import time as _t
    now = _t.monotonic()
    cutoff = now - _RL_UNKNOWN_WINDOW_S
    bucket = _rl_unknown_per_ip.get(client_ip, [])
    bucket = [t for t in bucket if t > cutoff]
    if len(bucket) >= _RL_UNKNOWN_MAX_PER_IP:
        _rl_unknown_per_ip[client_ip] = bucket
        return False
    bucket.append(now)
    _rl_unknown_per_ip[client_ip] = bucket
    # Cap the per-IP map too; same LRU trick.
    if len(_rl_unknown_per_ip) > _RL_BUCKETS_CAP:
        items = sorted(
            _rl_unknown_per_ip.items(),
            key=lambda kv: (kv[1][-1] if kv[1] else 0.0),
        )
        for ip, _ in items[: len(items) // 2]:
            _rl_unknown_per_ip.pop(ip, None)
    return True


def _client_ip(request: Request) -> str:
    """F-04/F-11 pattern: prefer cf-connecting-ip (CF-set, unforgeable from
    the buyer), fall back to the L4 peer.  Never trust X-Forwarded-For —
    that header is attacker-supplied."""
    cf = request.headers.get("cf-connecting-ip", "").strip()
    if cf:
        return cf
    return request.client.host if request.client else "unknown"


@router.api_route(
    "/mcp-proxy/{buyer_token}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
)
async def mcp_proxy(buyer_token: str, path: str, request: Request):
    # ── 1. Rate-limit FIRST (before DB lookup, to protect against unknown-token spam)
    # In-memory sliding window per token. Even unknown tokens get rate-limited.
    # 60 req/min/token = 1 RPS sustained, with full-burst tolerance.
    if not _rate_limit_check(buyer_token):
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limited", "detail": "Too many requests"},
            headers={"Retry-After": "10"},
        )

    # ── 2. Resolve buyer ──────────────────────────────────────────────────────
    buyer = await db.get_buyer(buyer_token)
    if not buyer:
        # F-13: cap unknown-token probes per source IP so an attacker cannot
        # cheaply enumerate or DB-flood by trying many random tokens.
        # Done AFTER the DB lookup so legit buyers (who always resolve) never
        # pay this cost, but BEFORE we 404 so the attacker actually hits 429.
        if not _unknown_token_ip_check(_client_ip(request)):
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "detail": "Too many requests"},
                headers={"Retry-After": "60"},
            )
        return JSONResponse(
            status_code=404,
            content={"error": "not_found"},
        )

    vps_ip = (buyer.get("vps_ip") or "").rstrip("/")
    if not vps_ip:
        # Return 404 (not 503) to avoid leaking whether the token exists vs whether
        # the buyer is mid-provisioning. Anti-enumeration: 404 = "this endpoint
        # cannot serve you", regardless of why.
        return JSONResponse(
            status_code=404,
            content={"error": "not_found"},
        )

    # ── 2. Wake up if paused ─────────────────────────────────────────────────
    if buyer.get("runtime_state") == "paused":
        ok = await _wake_up(buyer_token, buyer)
        if not ok:
            logger.error(
                "Wake-up timeout for token %.8s (vps_ip=%s)", buyer_token, vps_ip
            )
            return JSONResponse(
                status_code=504,
                content={
                    "error": "wake_timeout",
                    "detail": (
                        "Your Concerto environment is waking up. "
                        "Please retry in a few seconds."
                    ),
                },
            )

    # ── 3. Validate + build target URL (F-03 hardening) ──────────────────────
    internal_url, err = _safe_target_url(vps_ip, path)
    if err is not None:
        logger.warning(
            "Proxy rejecting unsafe path token=%.8s path=%r reason=%s",
            buyer_token, path, err,
        )
        return JSONResponse(
            status_code=400,
            content={"error": "bad_path", "detail": err},
        )

    # ── 4. Forward request ───────────────────────────────────────────────────
    try:
        response = await _forward(request, internal_url)
    except httpx.ConnectError as exc:
        logger.warning(
            "Proxy connect error for token %.8s path=%s: %s", buyer_token, path, exc
        )
        return JSONResponse(
            status_code=502,
            content={"error": "upstream_connect_failed", "detail": str(exc)},
        )
    except httpx.TimeoutException as exc:
        logger.warning(
            "Proxy timeout for token %.8s path=%s: %s", buyer_token, path, exc
        )
        return JSONResponse(
            status_code=504,
            content={"error": "upstream_timeout", "detail": str(exc)},
        )

    # ── 4. Update last_active_at (fire-and-forget) ───────────────────────────
    asyncio.create_task(
        db.update_buyer(buyer_token, last_active_at=int(time.time()))
    )

    return response


async def _wake_up(token: str, buyer: dict) -> bool:
    """Resume a paused NF service and wait for /healthz to return 200.

    Clears runtime_state in DB on success.  Returns True if ready, False on
    timeout.  Errors from the provider call are logged but don't abort — we
    still poll healthz in case NF resumes anyway.
    """
    vps_id = buyer.get("vps_id") or ""
    vps_ip = (buyer.get("vps_ip") or "").rstrip("/")
    healthz_url = f"{vps_ip}/healthz" if vps_ip else None

    logger.info(
        "Waking paused environment token=%.8s vps_id=%s", token, vps_id
    )
    t0 = time.monotonic()

    try:
        await provisioner.resume(api_key="", vps_id=vps_id)
    except Exception as exc:
        logger.error(
            "provider.resume failed token=%.8s vps_id=%s: %s — continuing poll",
            token, vps_id, exc,
        )

    if not healthz_url:
        logger.error("No vps_ip for token %.8s — cannot poll healthz", token)
        return False

    ready = await _poll_healthz(healthz_url, _WAKE_TIMEOUT_S)
    elapsed = time.monotonic() - t0

    if ready:
        await db.update_buyer(token, runtime_state=None)
        latency_ms = int(elapsed * 1000)
        await db.log_lifecycle_event("resume", token, vps_id=vps_id, resume_latency_ms=latency_ms, source="mcp_proxy_wake")
        logger.info(
            "Environment ready token=%.8s elapsed=%.1fs", token, elapsed
        )
    else:
        logger.error(
            "Wake-up timeout token=%.8s elapsed=%.1fs healthz_url=%s",
            token, elapsed, healthz_url,
        )

    return ready


async def _poll_healthz(url: str, timeout_s: float) -> bool:
    """Poll url until HTTP 200 or timeout.  Returns True if successful."""
    deadline = time.monotonic() + timeout_s
    async with httpx.AsyncClient(timeout=5) as client:
        while time.monotonic() < deadline:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(_POLL_INTERVAL_S)
    return False


async def _forward(request: Request, target_url: str) -> StreamingResponse:
    """Stream-proxy the request to target_url and return a StreamingResponse.

    The httpx client and upstream response are kept alive until the generator
    is exhausted; aclose() is called in the finally block.
    """
    out_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    body = await request.body()

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(_FORWARD_READ_S, connect=_FORWARD_CONNECT_S),
        follow_redirects=False,
    )

    upstream = await client.send(
        client.build_request(
            method=request.method,
            url=target_url,
            headers=out_headers,
            content=body,
            params=dict(request.query_params),
        ),
        stream=True,
    )

    # Filter hop-by-hop from response headers too
    resp_headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }

    async def _generate():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=4096):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        _generate(),
        status_code=upstream.status_code,
        headers=resp_headers,
        media_type=upstream.headers.get("content-type"),
    )
