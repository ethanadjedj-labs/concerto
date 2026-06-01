"""Draft generation rules: discloses maker, never auto-posts, angle is
chosen by matched signals."""
from __future__ import annotations

import time

from concerto.demand import drafts
from concerto.demand.models import Opportunity


def _opp(signals: list[str], source: str = "hn") -> Opportunity:
    return Opportunity(
        source=source,
        source_id="abc",
        url="https://example.com/x",
        title="test",
        body="An interesting demand-signal post body.",
        author="bob",
        author_context="comment",
        created_ts=int(time.time()),
        fetched_ts=int(time.time()),
        score=0.8,
        matched_signals=signals,
        rationale="t",
    )


def test_discloses_maker_affiliation_for_hn():
    body = drafts.draft_reply(_opp(["parallel-claude-code"], source="hn"))
    low = body.lower()
    assert "disclosure" in low or "maker" in low
    assert "concerto.run" in low
    assert "concerto" in low


def test_discloses_maker_affiliation_for_reddit():
    body = drafts.draft_reply(_opp(["claude-code-parallel"], source="reddit"))
    low = body.lower()
    assert "disclosure" in low
    assert "concerto.run" in low


def test_angle_for_parallel_signals():
    pkg = drafts.package(_opp(["parallel-claude-code", "tmux-pain"]))
    assert pkg["angle"] == "parallel"
    assert "tmux" in pkg["draft_reply"].lower() or "terminal" in pkg["draft_reply"].lower()


def test_angle_for_mcp_signals():
    pkg = drafts.package(_opp(["mcp-orchestration"]))
    assert pkg["angle"] == "mcp"


def test_generic_when_no_strong_signal():
    pkg = drafts.package(_opp(["explicit-question"]))  # intent-only
    assert pkg["angle"] == "generic"
    assert "Personalize" in pkg["draft_reply"]


def test_package_includes_url_and_score():
    pkg = drafts.package(_opp(["multi-agent"]))
    assert pkg["url"].startswith("https://")
    assert pkg["score"] == 0.8
    assert pkg["platform"] == "hn"
