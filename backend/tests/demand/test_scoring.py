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
