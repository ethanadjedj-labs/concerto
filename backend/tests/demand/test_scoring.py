"""Scoring should correctly rank Concerto-shaped demand vs noise."""
from __future__ import annotations

import time

from concerto.demand import scoring


NOW = int(time.time())


def test_classic_buyer_post_scores_high():
    title = "Anyone managed to run multiple Claude Code sessions in parallel?"
    body = (
        "I'm tired of juggling tmux panes. Is there a tool that lets me "
        "orchestrate Claude Code from a single chat? Looking for "
        "recommendations."
    )
    r = scoring.score_post(title, body, NOW)
    assert r.score > 0.5, f"expected > 0.5, got {r.score} ({r.rationale})"
    assert any(s.startswith("multiple-claude-code") or s.startswith("claude-code-parallel") for s in r.matched_signals)
    assert any(s.startswith("tmux-pain") or s.startswith("juggling-terminals") for s in r.matched_signals)


def test_unrelated_post_scores_zero():
    r = scoring.score_post(
        "Looking for a good Python web framework",
        "I want to build a small SaaS. FastAPI vs Django?",
        NOW,
    )
    assert r.score == 0.0
    assert r.rationale.startswith("no Concerto-core")


def test_negative_signal_drags_score_down():
    title = "Claude Status Update: degraded performance"
    body = "Anthropic posted an update about multi-agent claude code outage."
    r = scoring.score_post(title, body, NOW)
    assert r.score < 0.3, f"status-update bot noise should not rank high; got {r.score}"
    assert any("status-update-bot" in s for s in r.matched_signals)


def test_freshness_decays_old_posts():
    title = "How do I run multiple Claude Code instances in parallel?"
    body = "Looking for a tool to orchestrate them. Anyone using something?"
    fresh = scoring.score_post(title, body, NOW, now=NOW).score
    stale = scoring.score_post(title, body, NOW - 60 * 86400, now=NOW).score
    assert fresh > stale, f"fresh={fresh} stale={stale}"


def test_intent_amplifies_core_fit():
    base_title = "claude code orchestration"
    base_body = "thinking about multi-agent setups."
    with_q = scoring.score_post(
        base_title,
        base_body + " How do I get started? Looking for a tool.",
        NOW,
    ).score
    without_q = scoring.score_post(base_title, base_body, NOW).score
    assert with_q > without_q, f"intent should amplify: with={with_q} without={without_q}"


def test_ask_hn_hiring_monthly_is_suppressed():
    """The "Ask HN: Who wants to be hired?" monthly thread is a huge omnibus
    that matches Concerto signals by accident across thousands of comments.
    It should drop out of the top results entirely."""
    title = "Ask HN: Who wants to be hired? (May 2026)"
    # The aggregated comment text contains everything under the sun, including
    # genuine Concerto-shaped phrases that would otherwise score high.
    body = (
        "Resume: I built an mcp orchestration platform with multi-agent fleet "
        "support. Looking for new role. How can you reach me? "
        "Recommend you check my GitHub."
    )
    r = scoring.score_post(title, body, NOW)
    assert r.score < 0.2, (
        f"hiring-omnibus thread should not rank high; got {r.score} "
        f"signals={r.matched_signals}"
    )
    assert any("ask-hn-hiring-omnibus" in s for s in r.matched_signals)


def test_competitor_show_hn_is_downweighted():
    """A competitor's "Show HN: my parallel Claude Code tool" post is NOT
    buyer demand — engaging in its comments to push Concerto would be the
    exact spammy behavior the brand must avoid. Downweight."""
    title = "Show HN: AgentOS – Self-hosted web UI for managing multiple Claude Code sessions"
    body = "I built a tool to orchestrate multiple Claude Code processes."
    competitor = scoring.score_post(title, body, NOW)
    # Same content phrased as a buyer question should outrank it strongly.
    buyer_title = "Ask HN: how do I manage multiple Claude Code sessions?"
    buyer_body = "Looking for a tool to orchestrate. Any recommendations?"
    buyer = scoring.score_post(buyer_title, buyer_body, NOW)
    assert buyer.score > competitor.score, (
        f"buyer({buyer.score}) should outrank competitor-launch({competitor.score})"
    )
    assert any("competitor-show-hn" in s for s in competitor.matched_signals)


def test_competitor_negative_does_not_fire_on_body_show_hn_mention():
    """The 'Show HN:' anchor must only trigger on the *title* prefix —
    a buyer post that *quotes* a Show HN in the body should not be penalised."""
    title = "Ask HN: how do I manage parallel claude code sessions?"
    body = (
        "I saw a Show HN: AgentOS earlier but it didn't fit my workflow. "
        "Looking for a tool that handles MCP orchestration too."
    )
    r = scoring.score_post(title, body, NOW)
    assert not any("competitor-show-hn" in s for s in r.matched_signals), (
        f"competitor signal should be title-anchored; signals={r.matched_signals}"
    )
