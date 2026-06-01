"""Storage upsert/dedup behavior + draft persistence."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

from concerto.demand import storage
from concerto.demand.models import Opportunity


def _opp(source: str = "hn", source_id: str = "1", **k) -> Opportunity:
    return Opportunity(
        source=source,
        source_id=source_id,
        url=k.get("url", "https://news.ycombinator.com/item?id=1"),
        title=k.get("title", "demo"),
        body=k.get("body", ""),
        author=k.get("author", "alice"),
        author_context=k.get("author_context", "comment"),
        created_ts=k.get("created_ts", int(time.time())),
        fetched_ts=k.get("fetched_ts", int(time.time())),
        score=k.get("score", 0.5),
        matched_signals=k.get("matched_signals", ["foo"]),
        rationale=k.get("rationale", "test"),
    )


def test_upsert_new_then_update(tmp_path: Path):
    db = str(tmp_path / "demand.db")
    with storage.connect(db) as c:
        assert storage.upsert(c, _opp(score=0.3)) is True
        # Same dedup_key, higher score: should update, not duplicate.
        assert storage.upsert(c, _opp(score=0.9)) is False
        rows = list(c.execute("SELECT score FROM opportunities"))
        assert len(rows) == 1
        assert rows[0]["score"] == 0.9


def test_top_orders_by_score_desc(tmp_path: Path):
    db = str(tmp_path / "demand.db")
    with storage.connect(db) as c:
        storage.upsert(c, _opp(source_id="a", score=0.2))
        storage.upsert(c, _opp(source_id="b", score=0.9))
        storage.upsert(c, _opp(source_id="c", score=0.5))
        rows = storage.top_opportunities(c, limit=10, min_score=0.0)
        scores = [r["score"] for r in rows]
        assert scores == sorted(scores, reverse=True)


def test_min_score_filter(tmp_path: Path):
    db = str(tmp_path / "demand.db")
    with storage.connect(db) as c:
        storage.upsert(c, _opp(source_id="a", score=0.2))
        storage.upsert(c, _opp(source_id="b", score=0.7))
        rows = storage.top_opportunities(c, limit=10, min_score=0.5)
        assert len(rows) == 1
        assert rows[0]["source_id"] == "b"


def test_set_draft_persists(tmp_path: Path):
    db = str(tmp_path / "demand.db")
    with storage.connect(db) as c:
        opp = _opp(source_id="x")
        storage.upsert(c, opp)
        storage.set_draft(c, opp.dedup_key(), "draft body here")
        row = c.execute(
            "SELECT draft_reply, status FROM opportunities WHERE dedup_key=?",
            (opp.dedup_key(),),
        ).fetchone()
        assert row["draft_reply"] == "draft body here"
        assert row["status"] == "drafted"


def test_scan_runs_logged(tmp_path: Path):
    db = str(tmp_path / "demand.db")
    with storage.connect(db) as c:
        rid = storage.start_run(c, "hn")
        storage.finish_run(c, rid, fetched=10, accepted=7)
        row = c.execute("SELECT * FROM scan_runs WHERE id=?", (rid,)).fetchone()
        assert row["fetched"] == 10
        assert row["accepted"] == 7
        assert row["finished_ts"] is not None
        assert row["error"] is None
