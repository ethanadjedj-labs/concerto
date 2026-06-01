# Demand Radar — scorer v2 re-rank, 2026-06-01

The first real scan (turn 2) had real public URLs but the **top of the
ranking was polluted** by two classes of false positive:

1. **HN monthly omnibus threads** ("Ask HN: Who wants to be hired?",
   "Ask HN: What are you working on?"). These are huge threads where
   *some* comment inevitably matches Concerto-core phrases — but
   engaging at the omnibus level is meaningless.
2. **Competitor Show HN launches** ("Show HN: AgentOS – manage multiple
   Claude Code sessions"). Engaging in those comment threads to push
   Concerto is exactly the spammy promotion the brand must not do.

A side issue: HN comments inherited their **parent story's title**, so
the operator opening a "Ask HN: What are you working on?" link landed
on a single comment, not the omnibus. Misleading at best.

## Changes

| Change | File | Why |
| --- | --- | --- |
| New negative `ask-hn-hiring-omnibus` (weight -1.0) | `scoring.py` | Kill "Who wants to be hired?" / "Who is hiring?" / freelancer monthlies |
| New negative `ask-hn-working-omnibus` (weight -0.6) | `scoring.py` | Downweight "What are you working on?" monthlies (comments are still surfaceable if their own text scores high enough) |
| New negative `competitor-show-hn` (weight -0.45) | `scoring.py` | Downweight competitor launches in claude/agent/mcp/llm space |
| Title-anchored negatives accept `[comment in: …]` prefix | `scoring.py` | So the filter still fires when the parent omnibus is the comment's surrounding context |
| HN comments now titled `[comment in: <parent>] <snippet>` | `sources/hackernews.py` | Operator can tell at a glance they're looking at a comment, not the omnibus |
| `storage.upsert` refreshes title/body/author on re-scan | `storage.py` | Otherwise stale titles linger after scoring changes. Operator state (status, draft_reply, operator_note) is **preserved** |
| New `python -m concerto.demand.cli rescore` | `cli.py` | Re-apply scorer to all stored rows without burning API quota. Used to roll out scoring rule changes |
| +6 unit tests (4 scoring, 1 source, 1 storage) | `tests/demand/` | All 28 demand tests pass |

## Re-ranking impact

After `rescore` + HN re-fetch:

| dedup_key | title (truncated) | old | new | reason |
| --- | --- | --- | --- | --- |
| `hn:48066702` | Ask HN: Who wants to be hired? (May 2026) — [comment] | 0.88 | **0.00** | ask-hn-hiring-omnibus |
| `hn:46939513` | [comment in: Ask HN: What are you working on? (Feb 2026)] | 0.86 | **~0.25** | ask-hn-working-omnibus (not in top 12) |
| `hn:46533405` | Show HN: AgentOS – manage multiple Claude Code | 0.82 | **0.37** | competitor-show-hn |
| `hn:47978340` | Show HN: Omar – TUI for managing 100 coding agents | 0.79 | **0.34** | competitor-show-hn |
| `hn:47303711` | Show HN: ChatML – parallel Claude Code sessions | 0.79 | **0.34** | competitor-show-hn |
| `hn:47308676` | Show HN: Clausona – manage multiple Claude Code accounts | 0.74 | **0.29** | competitor-show-hn |

The new top of the ranking is dominated by **buyer-shaped content**:
`hn:48020416` (operator building an agentic OS, seeking pattern guidance),
`hn:47223928` (parallel coding agents with tmux + specs — discussion of
the *pain* Concerto solves), `hn:47511504` (multi-agent orchestration
in Claude Code — discussion), `hn:46578028` / `hn:44455918` / `hn:44178216`
(open-source orchestrator efforts, prime engagement surface).

A small residual: `hn:46939527` "Show HN: Claude Dashboard" still scores
0.69 because the competitor regex anchors on `agent | mcp | llm | claude
code | coding agent` — "Claude Dashboard / Claude sessions / tmux" slips
through. Left as-is to avoid over-fitting; operator can read the
`matched_signals` array and skip.

## Operator workflow (unchanged, except for rescore)

```bash
# Pull fresh demand from public sources (idempotent, polite rate)
.venv/bin/python -m concerto.demand.cli scan

# After editing scoring rules — re-apply without burning API quota
.venv/bin/python -m concerto.demand.cli rescore

# Top opportunities (default min-score=0.2)
.venv/bin/python -m concerto.demand.cli top -n 10 --min-score 0.5

# Operator hand-off packages with drafted replies
.venv/bin/python -m concerto.demand.cli package -n 5 --min-score 0.5 --save-drafts
```
