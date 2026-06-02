"""Operator-facing HTTP surface for the demand radar.

Goal-mapped to OUTCOME 4 ("operator hand-off"): the demand radar writes
findings into a queryable SQLite store at backend/demand.db. This router
exposes those findings over HTTP so the console / chat surface (or any
authenticated client) can read ranked opportunities, fetch a full
operator package with a drafted reply, and mark an opportunity as
posted / skipped — all without coupling to the SQLite file directly.

Endpoints
---------
  GET  /api/demand/stats
       counts by source / status, latest scan time per source.
  GET  /api/demand/top?n=10&min_score=0.5&status=new&source=hn
       ranked list of opportunities (no draft body, just the metadata).
  GET  /api/demand/opportunity/{dedup_key}
       single opportunity + full draft reply (full operator package).
  POST /api/demand/opportunity/{dedup_key}/status
       body: {"status": "posted", "note": "..."} — mark operator action.
  GET  /api/demand/runs?n=20
       recent scan_runs (audit trail — proves the radar is actually running).

Authentication
--------------
Same pattern as nf_admin_router: CONCERTO_OPS_TOKEN bearer or
?token=<OPS_TOKEN> query param. If the env var is unset, every endpoint
returns 503 — fail closed so a misconfigured deploy never leaks operator
context.

Read-only by design with one carefully scoped mutation (`/status`).
There is intentionally no "post this draft" endpoint — the system never
posts; only the operator does.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from concerto.demand import drafts, storage
from concerto.demand.models import Opportunity


router = APIRouter()

_OPS_TOKEN = os.getenv("CONCERTO_OPS_TOKEN", "")

_VALID_STATUSES = {"new", "reviewed", "drafted", "posted", "skipped"}


def _check_auth(request: Request, query_token: str = "") -> None:
    if not _OPS_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="CONCERTO_OPS_TOKEN not configured — set this env var to enable the demand API",
        )
    candidate = query_token
    if not candidate:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            candidate = auth_header[7:]
    # F-06: constant-time comparison so timing does not leak the token.
    import hmac as _hmac
    if not candidate or not _hmac.compare_digest(candidate, _OPS_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized — supply CONCERTO_OPS_TOKEN as Bearer token or ?token= param",
        )


def _row_to_metadata(row: Any) -> dict:
    """Compact dict for list views — no draft body, no rationale wall."""
    return {
        "dedup_key": row["dedup_key"],
        "source": row["source"],
        "source_id": row["source_id"],
        "url": row["url"],
        "title": row["title"],
        "author": row["author"],
        "author_context": row["author_context"],
        "created_ts": row["created_ts"],
        "fetched_ts": row["fetched_ts"],
        "score": row["score"],
        "matched_signals": json.loads(row["matched_signals"] or "[]"),
        "rationale": row["rationale"],
        "status": row["status"],
    }


def _row_to_opportunity(row: Any) -> Opportunity:
    return Opportunity(
        source=row["source"],
        source_id=row["source_id"],
        url=row["url"],
        title=row["title"],
        body=row["body"],
        author=row["author"],
        author_context=row["author_context"],
        created_ts=row["created_ts"],
        fetched_ts=row["fetched_ts"],
        score=row["score"],
        matched_signals=json.loads(row["matched_signals"] or "[]"),
        rationale=row["rationale"],
    )


@router.get("/api/demand/stats")
async def get_stats(request: Request, token: str = ""):
    _check_auth(request, token)
    with storage.connect() as conn:
        by_source = list(conn.execute(
            "SELECT source, COUNT(*) AS n FROM opportunities GROUP BY source ORDER BY n DESC"
        ))
        by_status = list(conn.execute(
            "SELECT status, COUNT(*) AS n FROM opportunities GROUP BY status ORDER BY n DESC"
        ))
        score_buckets = list(conn.execute(
            "SELECT "
            "  SUM(CASE WHEN score >= 0.7 THEN 1 ELSE 0 END) AS gte_0_7,"
            "  SUM(CASE WHEN score >= 0.5 AND score < 0.7 THEN 1 ELSE 0 END) AS s_0_5_to_0_7,"
            "  SUM(CASE WHEN score >= 0.3 AND score < 0.5 THEN 1 ELSE 0 END) AS s_0_3_to_0_5,"
            "  SUM(CASE WHEN score < 0.3 THEN 1 ELSE 0 END) AS lt_0_3 "
            "FROM opportunities"
        ))
        latest_runs = list(conn.execute(
            "SELECT source, MAX(started_ts) AS last_started, "
            "       MAX(finished_ts) AS last_finished "
            "FROM scan_runs GROUP BY source"
        ))
        total = conn.execute("SELECT COUNT(*) AS n FROM opportunities").fetchone()["n"]
    return {
        "total_opportunities": total,
        "by_source": [dict(r) for r in by_source],
        "by_status": [dict(r) for r in by_status],
        "score_buckets": [dict(r) for r in score_buckets][0] if score_buckets else {},
        "latest_runs": [dict(r) for r in latest_runs],
        "now": int(time.time()),
    }


@router.get("/api/demand/top")
async def get_top(
    request: Request,
    n: int = 10,
    min_score: float = 0.5,
    status: str | None = None,
    source: str | None = None,
    token: str = "",
):
    _check_auth(request, token)
    if n < 1 or n > 200:
        raise HTTPException(status_code=400, detail="n must be 1..200")
    if status is not None and status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {sorted(_VALID_STATUSES)}",
        )
    with storage.connect() as conn:
        q = "SELECT * FROM opportunities WHERE score >= ?"
        args: list[Any] = [min_score]
        if status is not None:
            q += " AND status = ?"
            args.append(status)
        if source is not None:
            q += " AND source = ?"
            args.append(source)
        q += " ORDER BY score DESC, created_ts DESC LIMIT ?"
        args.append(n)
        rows = list(conn.execute(q, args))
    return {
        "count": len(rows),
        "min_score": min_score,
        "status": status,
        "source": source,
        "results": [_row_to_metadata(r) for r in rows],
    }


@router.get("/api/demand/opportunity/{dedup_key}")
async def get_opportunity(dedup_key: str, request: Request, token: str = ""):
    _check_auth(request, token)
    with storage.connect() as conn:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE dedup_key = ?", (dedup_key,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"unknown dedup_key: {dedup_key}")
    meta = _row_to_metadata(row)
    pkg = drafts.package(_row_to_opportunity(row))
    # Prefer the operator's saved draft if present, otherwise the freshly
    # generated one. Either way the operator sees a draft they can edit.
    saved = row["draft_reply"]
    if saved:
        pkg["draft_reply"] = saved
        pkg["draft_source"] = "saved"
    else:
        pkg["draft_source"] = "generated"
    return {
        **meta,
        "body": row["body"],
        "operator_note": row["operator_note"],
        "package": pkg,
    }


class StatusUpdate(BaseModel):
    status: str = Field(..., description="new|reviewed|drafted|posted|skipped")
    note: str = Field("", description="optional operator note")


@router.post("/api/demand/opportunity/{dedup_key}/status")
async def post_status(
    dedup_key: str, body: StatusUpdate, request: Request, token: str = ""
):
    _check_auth(request, token)
    if body.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {sorted(_VALID_STATUSES)}",
        )
    with storage.connect() as conn:
        cur = conn.execute(
            "UPDATE opportunities SET status=?, operator_note=? WHERE dedup_key=?",
            (body.status, body.note, dedup_key),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"unknown dedup_key: {dedup_key}")
    return {"dedup_key": dedup_key, "status": body.status, "note": body.note}


@router.get("/api/demand/runs")
async def get_runs(request: Request, n: int = 20, token: str = ""):
    _check_auth(request, token)
    if n < 1 or n > 500:
        raise HTTPException(status_code=400, detail="n must be 1..500")
    with storage.connect() as conn:
        rows = list(conn.execute(
            "SELECT id, started_ts, finished_ts, source, fetched, accepted, error "
            "FROM scan_runs ORDER BY started_ts DESC LIMIT ?",
            (n,),
        ))
    return {
        "count": len(rows),
        "results": [dict(r) for r in rows],
    }
