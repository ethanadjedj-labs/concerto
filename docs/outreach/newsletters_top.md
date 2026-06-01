---
title: Top newsletters — Concerto outreach shortlist
status: ready-for-ethan (human DM/email only — agent does NOT send)
last_reviewed: 2026-06-01
---

# Top newsletters — Concerto outreach shortlist

Companion to [`creators_top10.md`](./creators_top10.md) (YouTubers + X accounts).
This file covers the **newsletter** axis — the highest-signal places where AI-coding
developers, MCP early adopters, and engineering leaders read about new tooling.

> **Why a separate file.** The original creator list skewed video/X. The goal
> explicitly calls out "PulseMCP and similar." Newsletters convert differently
> (longer dwell time, higher buyer intent, lower volume) and the outreach
> playbook for them is different (editorial pitch + free product access, not
> sponsored-segment pricing).

**Discipline:**
- Real, named, current outlets — no made-up audience numbers. Where a figure is
  inexact, it's marked `~`.
- Each entry has a **specific hook** that explains why Concerto is on-topic for
  *that* publication's readership — not a generic boilerplate.
- Nothing here gets sent autonomously by an agent. Every row is "ready for
  Ethan" to fire from his own identity.

---

## 1. PulseMCP — *The Agentic Loop* (formerly *PulseMCP Newsletter*)

| Field | Value |
|---|---|
| URL | https://www.pulsemcp.com/newsletter |
| Cadence | Bi-weekly |
| Audience | MCP early adopters: dev-tools builders, agent platform teams, infra people tracking the MCP spec |
| Contact | Editorial reply to a newsletter issue; or via the contact form on pulsemcp.com |
| Tier | **1 (primary)** |

**Why this newsletter, specifically:**
PulseMCP is the only English-language outlet whose entire editorial beat is *the
MCP ecosystem*. Their server directory at `pulsemcp.com/servers` is downstream
of the Official MCP Registry (per our research in
[`DISTRIBUTION.md`](../DISTRIBUTION.md#3-pulsemcp--pulsemcpcomservers)), so
Concerto will appear there automatically once Ethan runs `mcp-publisher
publish`. The newsletter is editorial on top of the directory — it surfaces
*interesting* servers, not all of them. Concerto's "orchestrate parallel Claude
Code over MCP" framing is genuinely novel within the MCP server taxonomy
(almost every other server is a data connector; Concerto is an *agent runtime*
exposed via MCP). That's a story worth a feature.

**Tailored hook:**

> "Hi PulseMCP — Concerto just landed in the Official MCP Registry
> (io.github.ethanadjedj-labs/concerto), so it should be in your next ingest.
> Quick pitch in case it's editorial-relevant: most MCP servers expose *data*.
> Concerto exposes *agents* — five tools (`start_claude_session`,
> `list_claude_sessions`, `get_claude_session`, `kill_claude_session`,
> `concerto_build`) that let a Claude chat orchestrate a fleet of long-running
> Claude Code sessions on a managed VPS. It's the first 'agent runtime over
> MCP' commercial server we've seen. Happy to give you a free Pro account
> ($99/mo SKU) to try and write about however you want — positive, critical, or
> not at all."

**Where Ethan sends this:** Reply to the most recent *Agentic Loop* issue from
his own email, OR via the contact form on https://www.pulsemcp.com/. Best
window: 2-3 days after the next Concerto release tag (so the registry listing
is fresh).

---

## 2. Latent Space (Smol AI News) — swyx & Alessio Fanelli

| Field | Value |
|---|---|
| URL | https://www.latent.space/ |
| Cadence | Weekly newsletter + podcast |
| Audience | AI engineers, foundation-model practitioners, AI infra builders |
| Contact | Editorial: `editor@latent.space`; podcast pitches via the website form |
| Tier | **1 (primary)** |

**Why this newsletter, specifically:**
Latent Space is the closest thing to "the AI Engineering trade publication." It
broke Claude Code coverage early — swyx noted at the AI Engineer conference
that the Claude Code track filled the largest room. The audience is the
*senior* end of AI engineers: people who actually buy infra. The editorial
angle that fits Concerto is **"what does team-level Claude Code infrastructure
look like in 2026?"** — a topic Latent Space has not yet covered in depth and
which their readers are actively asking about (DM evidence in the creators_top10
hook for swyx).

**Tailored hook:**

> "Hi Latent Space — Loved swyx's note from AI Engineer that the Claude Code
> track filled the largest room. We've been building the operator layer for
> teams adopting Claude Code at scale: Concerto (concerto.run) — an MCP server
> that exposes parallel Claude Code session management as five tools to a Claude
> chat. Solo $49 / Pro $99 / hosted multi-tenant via managed VPS. Pitch:
> editorial piece on 'agent runtimes over MCP' or a podcast segment on
> team-level Claude Code infrastructure. Free Pro accounts for you and Alessio
> regardless. Happy to write a guest piece on the engineering tradeoffs of
> per-customer remote MCP if that's a better fit."

**Where Ethan sends this:** Email `editor@latent.space` from Ethan's personal
address. Reference the AI Engineer keynote explicitly in the subject line —
makes it clear this isn't a cold blast.

---

## 3. The Pragmatic Engineer — Gergely Orosz

| Field | Value |
|---|---|
| URL | https://newsletter.pragmaticengineer.com/ |
| Cadence | Twice-weekly (free + paid tiers) |
| Audience | Engineering leaders, staff+ engineers, technical founders. Paid tier ~1M+ subs |
| Contact | `gergely@pragmaticengineer.com` (per his sponsor page); X DM @GergelyOrosz |
| Tier | **1 (primary)** |

**Why this newsletter, specifically:**
The Pragmatic Engineer is the leading newsletter for engineering management and
staff-level technical practice. Gergely has covered AI coding tools
extensively in 2025–2026 and his "Real-World Engineering Challenges" series is
exactly the format for a Concerto case study: a solo operator shipping
StrandedGrid (838K LOC, 1,064 commits, 6.5 weeks) using parallel Claude Code
orchestration — see [`CASE_STUDY_STRANDEDGRID.md`](../CASE_STUDY_STRANDEDGRID.md).
That's not a pitch; it's an actual engineering story. His audience are the
*decision-makers* for team adoption, not individual buyers.

**Tailored hook:**

> "Hi Gergely — long-time reader. Wanted to pitch a Real-World Engineering
> Challenges-style write-up: a solo dev (me) shipped a production data product
> (StrandedGrid — autonomous energy-sector intel daemon, $800 PDF over Stripe
> Connect) — 1,064 commits / ~838K LOC of Python in 6.5 weeks — by orchestrating
> 2-4 parallel Claude Code sessions over MCP. The orchestrator (Concerto) is
> itself a product I'm running ($49 Solo / $99 Pro). I'd write a 1,500-2,000-
> word piece with metrics reproducible from the repo (git log, LOC, ingester
> latency) — happy to make it editorial, no sponsorship, no quid pro quo. I
> realise the bar is high; the offer stands regardless."

**Where Ethan sends this:** Email `gergely@pragmaticengineer.com` from Ethan's
personal address with subject *"Pitch: solo dev ships 838K LOC of production
Python in 6.5 weeks — parallel Claude Code over MCP."* Include the case-study
markdown as an attached PDF.

---

## 4. TLDR AI (and TLDR Newsletter)

| Field | Value |
|---|---|
| URL | https://tldr.tech/ai (and https://tldr.tech for the daily dev digest) |
| Cadence | Daily |
| Audience | Mainstream developers + AI practitioners; ~500K+ subscribers (TLDR AI variant) |
| Contact | Sponsorship: `sponsors@tldr.tech` (rate card available); editorial: tip form on tldr.tech |
| Tier | **2 (sponsored or tip)** |

**Why this newsletter, specifically:**
TLDR's editorial format is a single 1-line summary of a tool, link, and short
"why it matters." Concerto fits cleanly: one sentence ("MCP server to run
multiple Claude Code sessions in parallel — orchestrate via Claude chat") and
a link. The free editorial slot is competitive but cheap to pitch; the
sponsorship slot has a published rate card and is a known-quantity channel for
dev tools at the $49–$99/mo price point. Ethan can run sponsorship economics
against expected conversion before committing.

**Tailored hook (editorial tip submission):**

> "Tool tip: Concerto (https://concerto.run). MCP server that lets a Claude
> chat orchestrate a fleet of parallel Claude Code sessions on a managed VPS.
> Five tools, persistent sessions, $49 Solo / $99 Pro. Built by one person who
> uses it daily to ship a production data product (StrandedGrid) in
> parallel-with-itself."

**Where Ethan sends this:** Tip form at https://tldr.tech for editorial; or
`sponsors@tldr.tech` for the sponsored slot (request the AI variant only).
Editorial is free, sponsored is ~$X (verify current rate). **Editorial first,
sponsored only if traction warrants.**

---

## 5. Ben's Bites

| Field | Value |
|---|---|
| URL | https://www.bensbites.com/ |
| Cadence | Daily |
| Audience | ~120K+ AI builders, founders, product people |
| Contact | Editorial submissions via https://bensbites.beehiiv.com/ submit form; sponsorship via the site |
| Tier | **2 (broad reach, lower per-click intent)** |

**Why this newsletter, specifically:**
Ben's Bites has one of the broadest English-language AI audiences and a
"tools" beat that is consistently the highest-clicked section. The audience is
a mix of developers and founders, so conversion is lower than PulseMCP or
Pragmatic Engineer but reach is meaningfully higher. The right angle for
Concerto is the **founder-buyer audience**, not the developer audience — the
"I built X in N weeks using parallel Claude Code orchestration" narrative
(StrandedGrid case study) is exactly what their readership engages with.

**Tailored hook:**

> "Hi Ben's Bites — submitting a tool for the daily roundup: Concerto
> (concerto.run). MCP-based orchestrator for parallel Claude Code sessions.
> Founder angle that might fit your audience better than the pure-dev pitch:
> I (solo founder, one person) used it to ship a production data product —
> StrandedGrid, autonomous energy-sector intel daemon — 1,064 commits in 6.5
> weeks. The orchestrator is the product. $49 / $99 SKUs. Happy to give
> free access to anyone you'd like to send to it."

**Where Ethan sends this:** Editorial submission form at
https://bensbites.beehiiv.com/. If picked up, link in the Tools section drives
~2-5K visits.

---

## 6. The Rundown AI

| Field | Value |
|---|---|
| URL | https://www.therundown.ai/ |
| Cadence | Daily |
| Audience | ~700K+ general AI audience; broader than developer-only |
| Contact | Sponsorship via https://www.therundown.ai/p/advertise; editorial form on site |
| Tier | **3 (broad awareness only)** |

**Why this newsletter, specifically:**
The Rundown is the largest English AI newsletter by raw audience. Concerto is
a developer tool, so the conversion rate on a Rundown placement will be
lower than PulseMCP / Pragmatic Engineer / Latent Space. **Listed here for
completeness and as a post-launch awareness channel after the dev-native
channels have been worked.** Do *not* lead with this — it's a fallback for
when there's already enough traction to absorb a low-intent traffic spike
without burning credibility.

**Tailored hook:** *(deferred — only worth crafting once Show HN and Product
Hunt have run and Concerto has live testimonials to attach.)*

---

## 7. AI Tidbits — Sahar Mor

| Field | Value |
|---|---|
| URL | https://www.aitidbits.ai/ |
| Cadence | Weekly |
| Audience | Applied AI engineers + AI product builders; ~30-50K range |
| Contact | Substack reply; or X DM @theaitidbits |
| Tier | **2 (high-fit, modest reach)** |

**Why this newsletter, specifically:**
Sahar's editorial focus is *applied AI engineering* — patterns, tools, and
architectures, not breaking-news links. Concerto's "agent runtime over MCP"
angle is a pattern, not a press release. Format fit is unusually strong.
Audience size is modest but qualitative — readers are people building real
production AI systems.

**Tailored hook:**

> "Hi Sahar — quick pitch for AI Tidbits. We built Concerto as an MCP server
> that exposes Claude Code sessions as tools to a Claude chat — turning the
> chat into a fleet orchestrator. Five tools, persistent VPS-hosted sessions,
> per-customer remote MCP via streamable-HTTP. The pattern feels novel enough
> to be worth a tidbit: 'agent runtimes as MCP servers.' Free Pro account
> regardless. Would also be happy to write a guest tidbit if that fits your
> editorial calendar."

**Where Ethan sends this:** Substack reply to the most recent issue, OR X DM
to @theaitidbits — Sahar publishes on Substack and X in parallel.

---

## Tier summary

| Tier | Outlets | Total addressable readers | Likely conversion intent |
|---|---|---|---|
| **1 (primary)** | PulseMCP · Latent Space · Pragmatic Engineer | ~150K MCP-aware + ~50K AI eng + ~1M paid eng leaders | **Very high** (on-topic, pre-qualified) |
| **2 (high-fit / modest reach)** | TLDR AI · Ben's Bites · AI Tidbits | ~500K + ~120K + ~40K | **Medium-high** (developer mix) |
| **3 (broad awareness)** | The Rundown AI | ~700K general AI | **Low** (broadcast only) |

**Recommended order of execution (for Ethan, post-launch):**

1. PulseMCP (immediately after the Official MCP Registry publish lands).
2. Latent Space (the week of Show HN — references the AI Engineer keynote).
3. Pragmatic Engineer (deeper pitch with the StrandedGrid case study attached).
4. TLDR AI editorial tip + AI Tidbits in parallel — both quick, low cost.
5. Ben's Bites once there's a Show HN comment thread to reference.
6. The Rundown only if a paid burst is wanted after #1-5 are working.

---

## Cross-references

- [`creators_top10.md`](./creators_top10.md) — YouTubers + X accounts (this
  file's companion).
- [`outreach_playbook.md`](./outreach_playbook.md) — the email/DM template
  library Ethan adapts the per-newsletter hooks into.
- [`../DISTRIBUTION.md`](../DISTRIBUTION.md) — registry-listing status; PulseMCP
  ingest is downstream of #1 in that table.
- [`../CASE_STUDY_STRANDEDGRID.md`](../CASE_STUDY_STRANDEDGRID.md) — the artifact
  the Pragmatic Engineer / Latent Space pitches both lean on.

---

## What this file is NOT

- It is **not** an autonomous-send queue. Every row is a hand-fired pitch from
  Ethan's identity, and the agent has not (and will not) impersonate him.
- It is **not** a sponsorship plan. Most rows are editorial or tip-form
  submissions; only TLDR AI and The Rundown explicitly carry sponsorship as a
  fallback path.
- Audience numbers are approximate and were not validated against the
  publishers' own analytics. Verify before quoting in any negotiation.
