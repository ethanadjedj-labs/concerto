"""Relevance scoring for Concerto-shaped demand.

We score on three orthogonal axes and combine into a single 0..1 score:

  1. CORE_FIT    — does the post talk about the exact pain Concerto solves?
                   (parallel/concurrent Claude Code, multi-agent orchestration,
                   long-running agents, MCP fleet, session persistence)
  2. BUYER_INTENT — is the author asking *for a tool / solution / help*, not
                   just musing? (question marks, "how do I", "anyone using",
                   "looking for", "tool that")
  3. FRESHNESS    — newer posts are more actionable. Decay over ~14 days.

The system tracks WHICH signals fired so the operator can see *why* a post
ranked highly. No fabricated signals — every match is a literal substring
hit in the public text.
"""
from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Signal definitions
# ---------------------------------------------------------------------------

# CORE_FIT signals — strong matches for Concerto's exact problem space.
# Each entry: (label, pattern, weight). Patterns are case-insensitive,
# matched as substrings on the lower-cased text (word-boundary aware where
# it matters).
_CORE_SIGNALS: list[tuple[str, str, float]] = [
    ("parallel-claude-code", r"\bparallel\b.{0,30}\bclaude code\b", 1.0),
    ("multiple-claude-code", r"\b(multiple|many|several|n\s+)\s+claude code\b", 1.0),
    ("claude-code-parallel", r"\bclaude code\b.{0,30}\b(parallel|concurrent|simultaneously|at once|in parallel)\b", 1.0),
    ("claude-code-orchestration", r"\bclaude code\b.{0,40}\b(orchestrat|fleet|swarm|farm|manage|coordinate)\w*", 0.9),
    ("agent-orchestration", r"\b(agent|claude|llm)\s*(orchestration|orchestrator|coordinator|fleet|swarm)\b", 0.7),
    ("multi-agent", r"\bmulti[-\s]?agent\b", 0.5),
    ("mcp-orchestration", r"\bmcp\b.{0,40}\b(orchestrat|server|fleet|registry|workflow)\w*", 0.6),
    ("mcp-server-build", r"\b(building|writing|wrote|made|made my own)\s+(an?\s+)?mcp\s+server\b", 0.5),
    ("session-persistence", r"\bsession\b.{0,30}\b(persist|resume|reattach|survive|crash|restart)\w*", 0.7),
    ("claude-code-managed", r"\b(hosted|managed|remote|cloud)\b.{0,30}\bclaude code\b", 0.8),
    ("claude-code-vps", r"\bclaude code\b.{0,30}\b(vps|server|ec2|droplet|remote machine)\b", 0.8),
    ("tmux-pain", r"\btmux\b.{0,80}\b(claude|agent|llm|copilot)\b", 0.6),
    ("background-agent", r"\b(background|long[-\s]running|overnight)\s+(agent|claude|task)s?\b", 0.5),
    ("juggling-terminals", r"\b(juggl|switch).{0,30}\b(terminal|window|claude|tab)s?\b", 0.6),
    ("context-switch-pain", r"\b(re[-\s]?prim(e|ing))\s+context\b", 0.7),
]

# BUYER_INTENT signals — author is asking for a solution / shopping.
_INTENT_SIGNALS: list[tuple[str, str, float]] = [
    ("explicit-question", r"\?", 0.2),
    ("how-do-i", r"\bhow (do|can|should) (i|we|you)\b", 0.5),
    ("looking-for-tool", r"\blooking for\b|\bsearching for\b|\bneed a\b|\bany tool\b|\bbest way to\b", 0.7),
    ("anyone-using", r"\b(anyone|anybody|has anyone|who|do you)\b.{0,30}\b(use|using|tried|recommend|know)\b", 0.5),
    ("recommendation-ask", r"\b(recommend|suggestion|advice|tips?|best practice)s?\b", 0.4),
    ("pain-statement", r"\b(struggling|frustrat|annoying|painful|tired of|hate|wish there was|wish i could)\b", 0.5),
    ("show-me-how", r"\b(workflow|setup|stack|how (do you|are you|are people))\b", 0.3),
]

# Negative signals — strong indicators the post is NOT a Concerto buyer.
_NEGATIVE_SIGNALS: list[tuple[str, str, float]] = [
    ("status-update-bot", r"\bclaude status update\b", -1.0),
    ("anthropic-meta", r"\banthropic\b.{0,40}\b(funding|raised|valuation|hires|ipo|acquires)\b", -0.5),
    ("model-comparison", r"\b(claude vs|gpt[-\s]?\d|gemini vs)\b", -0.3),
    ("jailbreak", r"\b(jailbreak|uncensored|nsfw|roleplay)\b", -0.5),
    ("hiring", r"\b(we[''']?re hiring|hiring engineers|job posting|apply now)\b", -0.5),
    # Hiring-monthly omnibus threads ("Ask HN: Who wants to be hired?",
    # "Ask HN: Who is hiring?"). The titles match Concerto-shaped phrases by
    # accident when concatenated with thousands of comments. Drop them outright.
    # The optional `[comment in: ...]` prefix is added by the HN source for
    # comments under such threads, so the anchor must skip past it.
    ("ask-hn-hiring-omnibus", r"^(\[comment in:\s*)?ask hn:\s*(who wants to be hired|who is hiring|freelancer)", -1.0),
    # Same shape for the "what are you working on" / "show off your project"
    # monthly omnibus — also pollutes with random comments.
    ("ask-hn-working-omnibus", r"^(\[comment in:\s*)?ask hn:\s*(what are you working on|show off|what['']s your)", -0.6),
    # Competitor-launch announcements. "Show HN" posts about claude / agents /
    # MCP are NOT buyer demand — they are peers announcing tools. Engaging in
    # those comments to push Concerto is the exact spammy behavior the brand
    # must avoid. Surface them in a separate competitor-watch view, not here.
    ("competitor-show-hn", r"^(\[comment in:\s*)?show hn:.{0,80}\b(claude code|claude[-\s]agent|agent|mcp|llm|coding agent)", -0.45),
]


@dataclass
class ScoreResult:
    score: float
    matched_signals: list[str]
    rationale: str


def _scan(text: str, signals: list[tuple[str, str, float]]) -> list[tuple[str, float]]:
    hits: list[tuple[str, float]] = []
    for label, pattern, weight in signals:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            hits.append((label, weight))
    return hits


def _freshness(created_ts: int, now: int | None = None) -> float:
    """Exponential decay: weight ~= exp(-age_days / 14). Floor at 0.1 for old
    but still-living threads."""
    if not created_ts:
        return 0.5
    now = now or int(time.time())
    age_days = max(0.0, (now - created_ts) / 86400.0)
    return max(0.1, math.exp(-age_days / 14.0))


def score_post(
    title: str,
    body: str,
    created_ts: int,
    *,
    now: int | None = None,
) -> ScoreResult:
    text = f"{title}\n{body}".lower()
    # Negative signals that key off the title prefix ("Show HN:", "Ask HN:")
    # must see the title at the start of the buffer. Match against the title
    # alone so prepended body text can't fool the anchor.
    title_only = title.lower().strip()

    core_hits = _scan(text, _CORE_SIGNALS)
    intent_hits = _scan(text, _INTENT_SIGNALS)
    neg_hits = _scan(text, _NEGATIVE_SIGNALS) + _scan(title_only, [
        s for s in _NEGATIVE_SIGNALS if s[1].startswith("^")
    ])
    # Dedup neg hits by label (a title-anchored signal may also match in text).
    seen_neg: set[str] = set()
    deduped_neg: list[tuple[str, float]] = []
    for label, w in neg_hits:
        if label in seen_neg:
            continue
        seen_neg.add(label)
        deduped_neg.append((label, w))
    neg_hits = deduped_neg

    # Sum core weights, capped at 1.0 (saturating).
    core_raw = sum(w for _, w in core_hits)
    core = min(1.0, core_raw / 1.5)  # ~1.5 cumulative weight saturates

    intent_raw = sum(w for _, w in intent_hits)
    intent = min(1.0, intent_raw / 1.0)

    neg = sum(w for _, w in neg_hits)  # already negative

    freshness = _freshness(created_ts, now=now)

    # Core fit is the dominant axis. A post must have *some* core fit to score
    # above noise. Intent and freshness modulate.
    base = core * (0.6 + 0.25 * intent + 0.15 * freshness)
    score = max(0.0, min(1.0, base + neg))

    all_hits = core_hits + intent_hits + neg_hits
    matched = [label for label, _ in all_hits]

    if not core_hits:
        rationale = "no Concerto-core signals matched"
    else:
        core_labels = ", ".join(label for label, _ in core_hits[:3])
        intent_labels = ", ".join(label for label, _ in intent_hits[:2])
        bits = [f"core: {core_labels}"]
        if intent_labels:
            bits.append(f"intent: {intent_labels}")
        bits.append(f"freshness: {freshness:.2f}")
        if neg_hits:
            bits.append("negatives: " + ", ".join(l for l, _ in neg_hits))
        rationale = " | ".join(bits)

    return ScoreResult(score=score, matched_signals=matched, rationale=rationale)
