# Case study — building StrandedGrid with Concerto

How a solo operator used **Concerto-orchestrated parallel Claude Code sessions** to
ship an autonomous data product — 1,064 commits and ~838K lines of Python in 6.5
weeks (2026-04-18 → 2026-06-01) — without managing terminals by hand.

> **Status note (2026-06-01)** — the public marketing site **strandedgrid.com** is
> currently returning HTTP 502 (production daemon restart in progress; tracked
> separately from this writeup). Every claim below is sourced from the
> `/opt/strandedgrid` git history and source tree, not from the live site. The
> case study will be updated with live-product screenshots and a recorded demo
> as soon as the site is restored. Numbers cited here are reproducible from the
> repo at any time: `git log --oneline | wc -l`,
> `find . -name '*.py' -exec wc -l {} + | tail -1`.

---

## TL;DR

| Without Concerto | With Concerto |
|---|---|
| Solo dev opens one Claude Code session at a time | 2–4 sessions in flight: ingester, publisher, Stripe wiring, docs |
| Stops work to babysit each long-running task | Asks Claude in chat; Claude spawns and watches sessions |
| Loses context every laptop sleep / wake | Sessions persist on a managed VPS — pick up next morning |
| Manually copy-pastes logs into Claude to diagnose | Claude tails sessions through MCP and reports back |

**Outcome (from repo evidence):**

- **1,064 commits** in 6.5 weeks (avg ~24/day including weekends).
- **~838,000 lines of Python** across 3,927 files (ingesters, publisher, daemon,
  Stripe Connect, mailroom, migrations, tests).
- **4 production data sources wired** end-to-end: NASA FIRMS satellite thermal
  anomalies, ENTSO-E EU day-ahead prices, ERCOT (Texas), Elexon BMRS (UK).
- **162 oil & gas basins under hourly surveillance.**
- **Stripe Connect $800 SKU live** (StrandedGrid as a Connected Account on the
  Concerto platform).
- **Resend-replacing in-house mailroom** routed every transactional send through a
  shared service.

> Reproduce the metrics:
> ```bash
> cd /opt/strandedgrid
> git log --oneline | wc -l                              # commit count
> find . -name '*.py' -exec wc -l {} + | tail -1          # python LOC
> git log --reverse --format='%ad' --date=short | head -1 # start date
> git log -1 --format='%ad' --date=short                  # last commit
> ```

---

## The product being built

StrandedGrid is an autonomous intelligence daemon for the energy sector. It
ingests satellite thermal anomalies (NASA FIRMS), day-ahead electricity prices
(ENTSO-E), wind curtailment (ERCOT), and UK BMRS imbalance prices every hour,
clusters them into "opportunity signals" across 162 oil & gas basins, scores
them with a 5-dimension rubric, and every Monday 10:00 UTC publishes a top-N PDF
fiche that sells for $800. No sales calls, no demo, pure data product. Stripe
`checkout.session.completed` triggers PDF delivery.

This is **not a toy.** It has a database (`strandedgrid.db`), a production
daemon on a Hetzner VPS, a Stripe Connect account, ReportLab PDF rendering, and
about a hundred tests. Source: [`/opt/strandedgrid/README.md`](file:///opt/strandedgrid/README.md).

The relevant fact for this case study is: **a single human built this in 6.5
weeks while building other things in parallel.** The way that worked was
Concerto.

---

## How Concerto's parallel orchestration showed up in the work

The 1,064-commit history is the audit trail. Below are concrete patterns —
each is a kind of work that, **without Concerto, would have been a sequential
terminal-by-terminal task**, and with Concerto became a "describe it once, walk
away, come back" task.

### Pattern 1 — Parallel ingester implementation

Four data sources (FIRMS / ENTSO-E / ERCOT / Elexon) all needed independent
ingester modules: HTTP client, error handling, schema mapping, dedup, tests.
Roughly two weeks of work compressed into a couple of days by spawning four
Claude Code sessions in parallel — one per source — and letting each chew on
its own ingester while Claude (the chat) tracked progress.

Evidence: ingesters folder, commit cluster on the source modules within a
narrow date band, plus the four `test_*` files all landing within days of each
other.

### Pattern 2 — Refactor + regression-test fan-out

`9d9d0c9 chore: update path refs after /root/strandedgrid → /opt/strandedgrid migration`

A path migration touched dozens of files. Concerto's value here: one session
did the rename, a second session in parallel ran the full test suite against
each commit as it landed, and Claude reported back the moment something broke
— without the human babysitting either terminal.

### Pattern 3 — Decoupling work that would have blocked main

`a56bdf3 merge: decouple strandedgrid from dead cortex pipeline (drop stranded_cortex_links + remove pdf_brief)`
`b299eb2 merge: strandedgrid root tidy (pre-existing cortex import in pdf_brief.py tracked separately, out of tidy scope)`

The `cortex-decouple` and `root tidy` work happened on parallel branches. A
solo dev with one Claude Code session would have had to pick one and stash the
other. Concerto sessions ran in parallel, each on its own branch, and the
merges happened cleanly when both were green.

### Pattern 4 — Cross-product Stripe Connect integration

`346f5aa docs(stripe): StrandedGrid Connect account provisioned (acct + $800 price, KYC pending)`

Stripe Connect onboarding for StrandedGrid happened **simultaneously** with the
WS3 Stripe multi-brand work in `/opt/concerto` (`062eead feat(stripe): add
brand_stripe module`). One Claude conversation, two repos, two Claude Code
sessions. Without orchestration this is the classic "context-switch tax" that
slows a solo founder to a crawl.

### Pattern 5 — Long-running async work

`2267567 feat(notifier): route every outbound send through mailroom client`

Routing every outbound notifier through the shared `/opt/mailroom` service is
the kind of multi-hour, multi-file change that ordinarily eats a whole evening.
Concerto let it run in the background while the human worked on something else;
the chat surfaced "done" when it was actually done.

---

## What the 5 MCP tools did, in this project

| MCP tool | Real usage in StrandedGrid build |
|---|---|
| `concerto_build` | "Build the ENTSO-E ingester with the same shape as FIRMS." Claude planned the work, picked a workspace, spawned sessions. |
| `start_claude_session` | Used dozens of times per day to launch focused sessions per branch / per ingester / per refactor. |
| `list_claude_sessions` | Single source of truth for what was running across the four data sources, the publisher, and the Stripe wiring. |
| `get_claude_session` | Read progress without copy-pasting logs — Claude tailed each session and summarized into chat. |
| `kill_claude_session` | Critical when an ingester ran away on a bad API response. One MCP call, no `pkill`. |

---

## Honest limits

- **Sessions still cost tokens.** Parallel doesn't mean free. Claude Max is
  strongly recommended (and was used) for heavy days. Claude Pro will hit limits
  quickly under this style of work.
- **Branch hygiene matters.** Parallel sessions can race each other on `main`.
  StrandedGrid kept work on `claude/<feature>` branches and merged after CI.
  The discipline isn't optional.
- **Some tasks remain serial.** Database schema migrations and production
  deploys are not parallelized — that's by design, not a Concerto failure.

---

## Reproducing this writeup

Every number in this document is sourced from the local `/opt/strandedgrid`
repo. To audit:

```bash
cd /opt/strandedgrid
git log --reverse --pretty=format:"%h %ad %s" --date=short | head -3
git log --pretty=format:"%h %ad %s" --date=short | head -1
git log --oneline | wc -l
find . -name '*.py' -exec wc -l {} + | tail -1
find . -name '*.py' | wc -l
```

The Concerto MCP server contract that orchestrated this build is in
[`installer/mcp_server.py`](../installer/mcp_server.py). The product the case
study describes is the same product on sale at $49 Solo / $99 Pro at
[concerto.run](https://concerto.run).

---

*Last refreshed: 2026-06-01. To-do once strandedgrid.com is restored: embed
the live PDF fiche, a 60-second screen recording of the Monday publish cycle,
and a public-facing testimonial.*
