# Concerto Demand Radar

A demand-capture system that scans public, ToS-compliant sources for posts
expressing Concerto-shaped demand (parallel Claude Code orchestration, MCP
fleet management, agent coordination pain) and surfaces ranked opportunities
to the operator with drafted, authentic, value-first reply templates.

> The system **detects and prepares**. A human **reviews and posts**. The
> code never posts on anyone's behalf. There are no fake personas, no
> sockpuppets, no auto-DM, no covert promotion.

---

## Why this exists (the demand-capture thesis)

Concerto's buyers are scattered across r/ClaudeAI, r/mcp, HN Show/Ask
threads, X dev-tool communities — small audiences but concentrated buying
intent. Manually combing those surfaces costs hours per day and misses 80%
of relevant posts. The radar inverts the funnel: it watches continuously,
scores every post against Concerto's exact problem space, and hands the
operator the top N each day with a *personalize-and-post* template.

A single high-fit reply on a 50-comment HN thread reliably out-converts a
$500 sponsored post. The radar's job is to surface those threads while
they're still fresh.

---

## Architecture

```
backend/concerto/demand/
├── __init__.py
├── models.py            Opportunity dataclass
├── storage.py           SQLite store at backend/demand.db
├── scoring.py           Three-axis relevance scorer (core / intent / freshness)
├── drafts.py            Template-based authentic-reply generator
├── cli.py               `python -m concerto.demand.cli <scan|top|package>`
└── sources/
    ├── __init__.py        Shared User-Agent
    ├── hackernews.py      HN Algolia API (no auth, public, programmatic)
    ├── reddit.py          Reddit public RSS (UA-identified, polite cadence)
    └── stackexchange.py   Stack Exchange 2.3 REST API (stackoverflow + ai.stackexchange)

backend/tests/demand/    Unit tests (19 tests, no network)
backend/demand.db        Findings store (separate from concerto.db)
docs/demand/             Reports + operator hand-off artifacts
```

The store schema lives in `storage.py`. The two tables are:

- `opportunities` — one row per detected post, dedup-keyed by
  `{source}:{source_id}`. Holds score, matched signals, rationale, the
  draft-reply, and an operator status (`new | reviewed | drafted | posted
  | skipped`).
- `scan_runs` — per-source audit log of every scan, fetched/accepted
  counts, and any error. Use this to verify the radar is actually running.

### Ethical + ToS guardrails (baked in)

| Rule | Where it's enforced |
| --- | --- |
| Only official APIs / public RSS | `sources/hackernews.py` (HN Algolia), `sources/reddit.py` (Reddit's published RSS). No scraping of logged-in surfaces. |
| Identified User-Agent | `sources/__init__.py` — UA names Concerto and links concerto.run. |
| Polite rate limits | `sources/reddit.py` sleeps 2–3s between subreddit fetches; HN Algolia queries serially. |
| No fake personas, no auto-post | The system *only* writes to the local SQLite store. There is no posting code, no DM code, no cross-platform identity. Operator posts manually. |
| Disclosed promotion | `drafts.py` always opens with `"Disclosure: I'm the maker of Concerto"`. |
| No fabricated demand | Every signal is a literal regex match on the public post text; the `matched_signals` list is auditable. |

---

## How to use it (operator workflow)

```bash
# 1. From /opt/concerto/backend, run a scan. Idempotent — re-runs upsert.
.venv/bin/python -m concerto.demand.cli scan

# 2. See the ranked list, score >= 0.4, top 10.
.venv/bin/python -m concerto.demand.cli top -n 10 --min-score 0.4

# 3. See full operator packages with drafted replies, persist the drafts
#    back to the DB (sets status='drafted'). Score threshold 0.5 by default.
.venv/bin/python -m concerto.demand.cli package -n 5 --min-score 0.5 --save-drafts
```

Each package contains:

- **url** — the live source link. Click it, read the actual thread.
- **author** + **author_context** — public handle + e.g. subreddit / HN points.
- **score** + **matched_signals** + **rationale** — why this ranked highly.
- **draft_reply** — markdown-ready text. Edit it. *Always* edit it. Replace
  the `[Personalize: ...]` block with a real callback to the thread. Then
  post AS yourself from your own account.

After posting, mark the opportunity in the DB so it doesn't keep
resurfacing:

```sql
UPDATE opportunities SET status='posted', operator_note='posted as @ethanadjedj 2026-06-01' WHERE dedup_key='hn:48066702';
```

The `status` column is the single source of truth for operator action. The
console / chat surface can later read this directly.

---

## Outcomes mapped

| Goal outcome | Where it lives |
| --- | --- |
| **1 — Demand radar** | `cli.py scan`. Fetches HN + Reddit, scores against Concerto's pain space, persists with live URLs, author context, timestamps, and a rationale per hit. First real scan: 189 HN + 25 Reddit, 98 with score ≥ 0.3 — see [`top_opportunities_2026-06-01.md`](./top_opportunities_2026-06-01.md). |
| **2 — Opportunity surfacing + drafted replies** | `cli.py package` + `drafts.py`. Produces a maker-disclosed, value-first, ranked-by-fit/freshness package the operator can edit and post. Real output: [`operator_packages_2026-06-01.md`](./operator_packages_2026-06-01.md). |
| **3 — Concerto's own authentic presence** | The brand voice already lives in `docs/distribution/` (HN post, Reddit post, Twitter threads, StrandedGrid case study, newsletters shortlist). The radar feeds *which threads* to engage on; the distribution assets supply the brand-account content cadence. The reply drafter explicitly *discloses the maker* in every output, so reuse-as-brand-account requires only one substitution. |
| **4 — Operator hand-off via Claude / console** | Findings live in `backend/demand.db`, a queryable SQLite store with a documented schema. The chat / console surface can read `opportunities WHERE status='new' ORDER BY score DESC` to feed the operator. We deliberately do **not** build a separate dashboard — the next step is to expose the same query as an MCP tool, which lets Claude in the console surface opportunities on demand. See [Future: MCP surface](#future-mcp-surface). |

---

## Source coverage + known limits

| Source | Mechanism | Status |
| --- | --- | --- |
| Hacker News | Algolia API (`hn.algolia.com/api/v1/search`) | Working — 189 hits/scan across 10 queries |
| Reddit (r/ClaudeAI, r/mcp, …) | Public Atom RSS, UA-identified | Partial — Reddit IP-blocks data-center IPs on many endpoints (returns 403). r/ClaudeAI works from this VPS; r/mcp, r/cursor, r/LocalLLaMA, r/SaaS, r/ChatGPTCoding return 403. **Operator can fix** by setting `CONCERTO_REDDIT_CLIENT_ID` / `CONCERTO_REDDIT_CLIENT_SECRET` and switching to OAuth — see "Adding OAuth Reddit" below |
| Stack Exchange (stackoverflow.com + ai.stackexchange.com) | Public REST API 2.3 (`api.stackexchange.com/2.3/search/advanced`) | Working — first scan returned 9 hits / 8 queries / 2 sites. Top hit `so:79827749` (multi-agent bearer-token, score 0.54), one Claude-Code specific question (`so:79927051`). Set `CONCERTO_STACKEXCHANGE_KEY` to raise quota from 300→10,000 req/day. |
| X / Twitter | Official API requires paid tier | Deliberately deferred — paid-only API access is too constrained for the score-everything model. Operator monitors X manually from the [creator shortlist](../outreach/creators_top10.md). |

### Adding OAuth Reddit (operator action)

1. Create a Reddit app at https://www.reddit.com/prefs/apps (type: `script`).
2. Set env vars on the Concerto VPS:
   ```bash
   export CONCERTO_REDDIT_CLIENT_ID=...
   export CONCERTO_REDDIT_CLIENT_SECRET=...
   export CONCERTO_REDDIT_USERNAME=concerto-radar  # the brand account
   export CONCERTO_REDDIT_PASSWORD=...
   ```
3. A later turn will add `sources/reddit_oauth.py` reading those vars. The
   current RSS path remains as the no-credential fallback.

---

## Future: MCP surface

The natural follow-up is to expose the demand store via the same MCP that
Concerto already uses. A skeleton:

```python
# proposed backend/concerto/demand/mcp_router.py
@mcp_tool("list_demand_opportunities")
def list_demand_opportunities(min_score: float = 0.5, status: str = "new", n: int = 10):
    with storage.connect() as c:
        return [drafts.package(opp) for opp in storage.top_opportunities(c, n, min_score, status)]

@mcp_tool("mark_demand_opportunity")
def mark_demand_opportunity(dedup_key: str, status: str, note: str = ""):
    with storage.connect() as c:
        c.execute("UPDATE opportunities SET status=?, operator_note=? WHERE dedup_key=?", (status, note, dedup_key))
```

With those two tools wired to the existing Concerto MCP server, the
operator can — *from inside any Claude chat* — say "show me today's top 5
demand opportunities" and "mark the HN one as posted." That is OUTCOME 4
in its strongest form. It is deliberately left for a separate turn so
this turn's diff stays reviewable.

---

## Cron / continuous operation

For continuous capture, the operator runs:

```cron
*/30 * * * * cd /opt/concerto/backend && .venv/bin/python -m concerto.demand.cli scan >> /var/log/concerto/demand-radar.log 2>&1
```

A 30-minute cadence is well under any source's published rate limits and
keeps Reddit/HN ranges fresh. Findings accumulate into `demand.db`; the
operator queries on demand.

---

## Anti-bullshit ledger

- All 189+ HN hits in the first real scan are **real public URLs**. Click
  any of them — they resolve.
- The `matched_signals` array for every opportunity is a list of regex
  labels that literally fired against the post text. There is no LLM
  hallucinating "this looks like demand" — every match is auditable.
- The draft-reply generator is **template-based**, not LLM-generated. We
  do not fabricate product claims; the only Concerto-specific copy is the
  TL;DR string in `drafts.py:CONCERTO_TLDR`.
- The system has **never posted anything** and contains no posting code.
- See the first real run on `2026-06-01`:
  [`top_opportunities_2026-06-01.md`](./top_opportunities_2026-06-01.md),
  [`operator_packages_2026-06-01.md`](./operator_packages_2026-06-01.md).
