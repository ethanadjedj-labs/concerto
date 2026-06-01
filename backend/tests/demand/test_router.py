"""HTTP API tests for the demand router.

Each test seeds an isolated demand.db (via the CONCERTO_DEMAND_DB env
var) and runs against a FastAPI TestClient. The auth pattern matches
nf_admin_router (CONCERTO_OPS_TOKEN bearer or ?token= query).
"""
from __future__ import annotations

import importlib
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from concerto.demand import storage
from concerto.demand.models import Opportunity


def _seeded_app(tmp_path: Path, ops_token: str = "test-token") -> TestClient:
    """Build a fresh FastAPI app + isolated demand.db with a couple of opps."""
    db_path = tmp_path / "demand.db"
    import os
    os.environ["CONCERTO_DEMAND_DB"] = str(db_path)
    os.environ["CONCERTO_OPS_TOKEN"] = ops_token

    # Reimport the router so it picks up the new OPS_TOKEN.
    import concerto.demand_router as mod
    importlib.reload(mod)

    with storage.connect(str(db_path)) as conn:
        storage.upsert(conn, Opportunity(
            source="hn", source_id="100",
            url="https://news.ycombinator.com/item?id=100",
            title="Show HN: parallel claude sessions",
            body="how do you run multiple claude code agents?",
            author="alice", author_context="story",
            created_ts=int(time.time()) - 3600,
            fetched_ts=int(time.time()),
            score=0.82, matched_signals=["parallel-claude-code"],
            rationale="core: parallel | intent: explicit-question",
        ))
        storage.upsert(conn, Opportunity(
            source="reddit", source_id="abc",
            url="https://www.reddit.com/r/ClaudeAI/comments/abc/",
            title="MCP orchestration question",
            body="anyone built an MCP that orchestrates claude code?",
            author="bob", author_context="r/ClaudeAI",
            created_ts=int(time.time()) - 7200,
            fetched_ts=int(time.time()),
            score=0.55, matched_signals=["mcp-orchestration"],
            rationale="core: mcp",
        ))
        storage.upsert(conn, Opportunity(
            source="hn", source_id="200",
            url="https://news.ycombinator.com/item?id=200",
            title="Unrelated low-score post",
            body="",
            author="carol", author_context="story",
            created_ts=int(time.time()),
            fetched_ts=int(time.time()),
            score=0.15, matched_signals=[],
            rationale="",
        ))
        storage.start_run(conn, "hn")

    app = FastAPI()
    app.include_router(mod.router)
    return TestClient(app)


@pytest.fixture
def client(tmp_path):
    return _seeded_app(tmp_path)


# ── auth ────────────────────────────────────────────────────────────────────

def test_auth_required_no_token(client):
    r = client.get("/api/demand/top")
    assert r.status_code == 401


def test_auth_query_param_works(client):
    r = client.get("/api/demand/top?token=test-token")
    assert r.status_code == 200


def test_auth_bearer_header_works(client):
    r = client.get("/api/demand/top", headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 200


def test_auth_wrong_token_rejected(client):
    r = client.get("/api/demand/top", headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401


def test_auth_fails_closed_when_unset(tmp_path, monkeypatch):
    # When CONCERTO_OPS_TOKEN is unset, every endpoint must 503 — fail
    # closed so a misconfigured deploy never leaks the operator surface.
    import os
    db_path = tmp_path / "demand.db"
    os.environ["CONCERTO_DEMAND_DB"] = str(db_path)
    monkeypatch.delenv("CONCERTO_OPS_TOKEN", raising=False)
    import concerto.demand_router as mod
    importlib.reload(mod)
    app = FastAPI()
    app.include_router(mod.router)
    c = TestClient(app)
    r = c.get("/api/demand/top")
    assert r.status_code == 503


# ── top ─────────────────────────────────────────────────────────────────────

def test_top_default_score_threshold(client):
    r = client.get("/api/demand/top?token=test-token")
    assert r.status_code == 200
    data = r.json()
    # Default min_score=0.5 → only the two high-score rows.
    assert data["count"] == 2
    # Ordered by score desc.
    scores = [x["score"] for x in data["results"]]
    assert scores == sorted(scores, reverse=True)


def test_top_filter_by_source(client):
    r = client.get("/api/demand/top?token=test-token&source=hn&min_score=0.0")
    assert r.status_code == 200
    data = r.json()
    assert all(x["source"] == "hn" for x in data["results"])
    assert data["count"] == 2


def test_top_filter_by_status(client):
    r = client.get("/api/demand/top?token=test-token&status=new&min_score=0.0")
    assert r.status_code == 200
    assert all(x["status"] == "new" for x in r.json()["results"])


def test_top_rejects_invalid_status(client):
    r = client.get("/api/demand/top?token=test-token&status=bogus")
    assert r.status_code == 400


def test_top_rejects_oob_n(client):
    r = client.get("/api/demand/top?token=test-token&n=0")
    assert r.status_code == 400
    r = client.get("/api/demand/top?token=test-token&n=999")
    assert r.status_code == 400


def test_top_strips_body_for_compactness(client):
    r = client.get("/api/demand/top?token=test-token&min_score=0.0")
    assert r.status_code == 200
    for x in r.json()["results"]:
        assert "body" not in x  # list view is compact
        assert "matched_signals" in x
        assert isinstance(x["matched_signals"], list)


# ── opportunity (full package) ─────────────────────────────────────────────

def test_opportunity_returns_full_package(client):
    r = client.get("/api/demand/opportunity/hn:100?token=test-token")
    assert r.status_code == 200
    data = r.json()
    assert data["dedup_key"] == "hn:100"
    assert "body" in data  # full view includes body
    assert "package" in data
    pkg = data["package"]
    assert pkg["draft_source"] == "generated"
    assert "draft_reply" in pkg
    assert "concerto.run" in pkg["draft_reply"].lower()
    # Disclosure is mandatory — guard the brand promise here.
    assert "maker" in pkg["draft_reply"].lower() or "built" in pkg["draft_reply"].lower()


def test_opportunity_uses_saved_draft_if_present(client, tmp_path):
    import os
    db_path = os.environ["CONCERTO_DEMAND_DB"]
    with storage.connect(db_path) as conn:
        storage.set_draft(conn, "hn:100", "CUSTOM OPERATOR DRAFT", status="drafted")
    r = client.get("/api/demand/opportunity/hn:100?token=test-token")
    assert r.status_code == 200
    pkg = r.json()["package"]
    assert pkg["draft_source"] == "saved"
    assert pkg["draft_reply"] == "CUSTOM OPERATOR DRAFT"


def test_opportunity_404_on_unknown_key(client):
    r = client.get("/api/demand/opportunity/hn:DOES_NOT_EXIST?token=test-token")
    assert r.status_code == 404


# ── status mutation ────────────────────────────────────────────────────────

def test_status_update_persists(client):
    r = client.post(
        "/api/demand/opportunity/hn:100/status?token=test-token",
        json={"status": "posted", "note": "posted as @me 2026-06-01"},
    )
    assert r.status_code == 200
    # Verify it actually persisted.
    r2 = client.get("/api/demand/opportunity/hn:100?token=test-token")
    assert r2.json()["status"] == "posted"
    assert r2.json()["operator_note"] == "posted as @me 2026-06-01"


def test_status_update_rejects_invalid_status(client):
    r = client.post(
        "/api/demand/opportunity/hn:100/status?token=test-token",
        json={"status": "lol", "note": ""},
    )
    assert r.status_code == 400


def test_status_update_404_on_unknown_key(client):
    r = client.post(
        "/api/demand/opportunity/hn:UNKNOWN/status?token=test-token",
        json={"status": "posted", "note": ""},
    )
    assert r.status_code == 404


# ── stats + runs ───────────────────────────────────────────────────────────

def test_stats_reports_counts(client):
    r = client.get("/api/demand/stats?token=test-token")
    assert r.status_code == 200
    data = r.json()
    assert data["total_opportunities"] == 3
    sources = {row["source"]: row["n"] for row in data["by_source"]}
    assert sources == {"hn": 2, "reddit": 1}
    statuses = {row["status"]: row["n"] for row in data["by_status"]}
    assert statuses.get("new") == 3
    assert data["score_buckets"]["gte_0_7"] == 1
    assert "now" in data


def test_runs_returns_recent_scans(client):
    r = client.get("/api/demand/runs?token=test-token")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    assert data["results"][0]["source"] == "hn"
