"""F-07 — Ops token must not be accepted as a `?token=` query param on
JSON `/api/admin/*` or `/api/demand/*` endpoints.

Tokens in the query string leak into:
  * web-server access logs,
  * Cloudflare access logs,
  * browser history,
  * Referer headers to cross-origin assets the page loads.

Hardened contract:
  * The HTML dashboard route at `/api/admin/nf-status/page` STILL accepts
    `?token=` (so admins can bookmark it; JS reads + immediately strips).
  * Every JSON API route requires the `Authorization: Bearer` header and
    rejects `?token=` with 401 even if the value is correct — so a stale
    bookmark, a piece of glue code, or a misconfigured curl pipeline does
    not write the token to disk in the wrong place.
"""
from __future__ import annotations

import importlib
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient


_OPS_TOKEN = "f07-test-token-abc123"


def _make_app(module_name: str):
    os.environ["CONCERTO_OPS_TOKEN"] = _OPS_TOKEN
    mod = importlib.import_module(module_name)
    importlib.reload(mod)
    app = FastAPI()
    app.include_router(mod.router)
    return TestClient(app, raise_server_exceptions=False), mod


# ── nf_admin_router ──────────────────────────────────────────────────────────


def test_f07_admin_json_rejects_query_token():
    client, _mod = _make_app("concerto.nf_admin_router")

    r = client.get(f"/api/admin/nf-status?token={_OPS_TOKEN}")
    assert r.status_code == 401, (
        f"F-07: /api/admin/nf-status accepted ?token= in the query string "
        f"(status={r.status_code}, body={r.text[:200]!r}).  Tokens in URLs "
        f"leak into access logs, browser history, and Referer headers."
    )


def test_f07_admin_json_accepts_bearer():
    client, _mod = _make_app("concerto.nf_admin_router")

    # Bearer header still works — we only forbid the query param.
    # The endpoint will likely 500 trying to hit NF (no API token), so
    # accept anything that is NOT a 401/403 — we're asserting the auth
    # gate let us through.
    r = client.get(
        "/api/admin/nf-status",
        headers={"Authorization": f"Bearer {_OPS_TOKEN}"},
    )
    assert r.status_code not in (401, 403), (
        f"F-07 regression: bearer-header auth must still work "
        f"(status={r.status_code}, body={r.text[:200]!r})"
    )


def test_f07_admin_page_still_accepts_query_token():
    """The HTML dashboard route is the ergonomic exception — bookmarking is
    only possible via the query param."""
    client, _mod = _make_app("concerto.nf_admin_router")

    r = client.get(f"/api/admin/nf-status/page?token={_OPS_TOKEN}")
    assert r.status_code == 200, (
        f"F-07 over-correction: the HTML dashboard page must still accept "
        f"?token= for bookmarking (status={r.status_code})"
    )


# ── demand_router ────────────────────────────────────────────────────────────


def test_f07_demand_json_rejects_query_token():
    client, _mod = _make_app("concerto.demand_router")

    # Use /stats — read-only, no body, no DB dependencies in the auth path.
    r = client.get(f"/api/demand/stats?token={_OPS_TOKEN}")
    assert r.status_code == 401, (
        f"F-07: /api/demand/stats accepted ?token= in the query string "
        f"(status={r.status_code}, body={r.text[:200]!r})."
    )


def test_f07_demand_json_accepts_bearer():
    client, _mod = _make_app("concerto.demand_router")

    r = client.get(
        "/api/demand/stats",
        headers={"Authorization": f"Bearer {_OPS_TOKEN}"},
    )
    # Auth passes — endpoint may 500 due to missing demand.db in tests, but
    # the contract under test is "bearer gets past the gate".
    assert r.status_code != 401, (
        f"F-07 regression: demand bearer-header auth must still work "
        f"(status={r.status_code}, body={r.text[:200]!r})"
    )
