"""SQLite store for demand-radar findings.

Schema is deliberately separate from concerto.db so a corruption or
schema migration here cannot affect the billing/provisioning core.
Default path: backend/demand.db relative to this file's repo root.

Operator hand-off (OUTCOME 4): findings are queryable by anyone with
sqlite3 access. A later turn will surface them through the chat/console
surface; this store is the canonical source.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import Opportunity


_SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    dedup_key   TEXT PRIMARY KEY,        -- "{source}:{source_id}"
    source      TEXT NOT NULL,
    source_id   TEXT NOT NULL,
    url         TEXT NOT NULL,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL DEFAULT '',
    author      TEXT NOT NULL DEFAULT '',
    author_context TEXT NOT NULL DEFAULT '',
    created_ts  INTEGER NOT NULL,
    fetched_ts  INTEGER NOT NULL,
    score       REAL NOT NULL DEFAULT 0,
    matched_signals TEXT NOT NULL DEFAULT '[]',
    rationale   TEXT NOT NULL DEFAULT '',
    fingerprint TEXT NOT NULL,
    -- Operator hand-off state
    status      TEXT NOT NULL DEFAULT 'new', -- new|reviewed|drafted|posted|skipped
    draft_reply TEXT NOT NULL DEFAULT '',
    operator_note TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_opp_score ON opportunities(score DESC, created_ts DESC);
CREATE INDEX IF NOT EXISTS idx_opp_source ON opportunities(source);
CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);

CREATE TABLE IF NOT EXISTS scan_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_ts  INTEGER NOT NULL,
    finished_ts INTEGER,
    source      TEXT NOT NULL,
    fetched     INTEGER NOT NULL DEFAULT 0,
    accepted    INTEGER NOT NULL DEFAULT 0,
    error       TEXT
);
"""


def default_db_path() -> str:
    # backend/demand.db, alongside concerto.db
    backend_dir = Path(__file__).resolve().parents[2]
    return str(backend_dir / "demand.db")


@contextmanager
def connect(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or os.environ.get("CONCERTO_DEMAND_DB") or default_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert(conn: sqlite3.Connection, opp: Opportunity) -> bool:
    """Insert or update an opportunity. Returns True if newly inserted."""
    fp = opp.fingerprint()
    cur = conn.execute(
        "SELECT fingerprint, score FROM opportunities WHERE dedup_key=?",
        (opp.dedup_key(),),
    )
    row = cur.fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO opportunities
               (dedup_key, source, source_id, url, title, body, author,
                author_context, created_ts, fetched_ts, score, matched_signals,
                rationale, fingerprint)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                opp.dedup_key(),
                opp.source,
                opp.source_id,
                opp.url,
                opp.title,
                opp.body,
                opp.author,
                opp.author_context,
                opp.created_ts,
                opp.fetched_ts,
                opp.score,
                json.dumps(opp.matched_signals),
                opp.rationale,
                fp,
            ),
        )
        return True
    # Update score/rationale/fingerprint in case scoring rules changed.
    conn.execute(
        """UPDATE opportunities
           SET score=?, matched_signals=?, rationale=?, fingerprint=?, fetched_ts=?
           WHERE dedup_key=?""",
        (
            opp.score,
            json.dumps(opp.matched_signals),
            opp.rationale,
            fp,
            opp.fetched_ts,
            opp.dedup_key(),
        ),
    )
    return False


def start_run(conn: sqlite3.Connection, source: str) -> int:
    cur = conn.execute(
        "INSERT INTO scan_runs(started_ts, source) VALUES(?, ?)",
        (int(time.time()), source),
    )
    return cur.lastrowid


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    fetched: int,
    accepted: int,
    error: str | None = None,
) -> None:
    conn.execute(
        """UPDATE scan_runs SET finished_ts=?, fetched=?, accepted=?, error=?
           WHERE id=?""",
        (int(time.time()), fetched, accepted, error, run_id),
    )


def top_opportunities(
    conn: sqlite3.Connection,
    limit: int = 20,
    min_score: float = 0.0,
    status: str | None = None,
) -> list[sqlite3.Row]:
    q = "SELECT * FROM opportunities WHERE score >= ?"
    args: list = [min_score]
    if status is not None:
        q += " AND status = ?"
        args.append(status)
    q += " ORDER BY score DESC, created_ts DESC LIMIT ?"
    args.append(limit)
    return list(conn.execute(q, args))


def set_draft(
    conn: sqlite3.Connection, dedup_key: str, draft: str, status: str = "drafted"
) -> None:
    conn.execute(
        "UPDATE opportunities SET draft_reply=?, status=? WHERE dedup_key=?",
        (draft, status, dedup_key),
    )
