# X/Twitter — Launch Thread (variant C: StrandedGrid receipts)

> **Where Ethan posts this:** from @ConcertoRun, with a quote-tweet from Ethan's
> personal handle within the first hour. Post 48–72h after variant A so the
> launch narrative breathes, then this thread compounds it with proof.
> Best windows: Tue–Thu 9–11am ET. Pin if it outperforms variant A.

8 tweets. Each ≤280 chars. Receipts-first angle for the "show me proof" reader
who bounced off the abstract pitch of variant A. Anchored in the real
`/opt/strandedgrid` repo — every number is reproducible from
[`docs/CASE_STUDY_STRANDEDGRID.md`](../CASE_STUDY_STRANDEDGRID.md).

---

**Tweet 1 — Hook**

> 1,064 commits.
> ~838,000 lines of Python.
> 6.5 weeks.
> One person.
>
> No, it wasn't vibe coding. It was Claude Code orchestrated through MCP — and
> the orchestrator is the product.
>
> 🧵

*[230 chars]*

---

**Tweet 2 — What was actually shipped**

> The product: StrandedGrid — autonomous intel daemon for the energy sector.
>
> Ingests 4 live sources (NASA FIRMS / ENTSO-E / ERCOT / Elexon BMRS), scores
> 162 oil & gas basins hourly, publishes a weekly $800 PDF via Stripe Connect.
>
> Real DB. Real prod. Not a demo.

*[266 chars]*

---

**Tweet 3 — Why Claude Code alone wasn't enough**

> Claude Code can build any one of those pieces fast.
>
> Building 4 ingesters + a publisher + Stripe + a mailroom **at the same time**
> as a solo dev means juggling 4 tmux panes, losing context every laptop sleep,
> and copy-pasting logs into chat to debug.
>
> That breaks down.

*[277 chars]*

---

**Tweet 4 — The pattern that actually worked**

> Pattern that built StrandedGrid in 6.5 weeks:
>
> 1. Ask Claude (in chat) to spawn 2–4 Claude Code sessions
> 2. Each session works on its own slice on the VPS
> 3. Claude tails them through MCP and reports back
> 4. I touch zero terminals
>
> That's all Concerto is.

*[265 chars]*

---

**Tweet 5 — Concrete: parallel ingester sprint**

> Receipts. Day 12 of the build:
>
> – sess_A: NASA FIRMS ingester
> – sess_B: ENTSO-E day-ahead prices
> – sess_C: ERCOT wind curtailment
> – sess_D: Elexon BMRS UK imbalance
>
> All four ingesters drafted in one afternoon. Hand-written, would've taken a
> week.

*[260 chars]*

---

**Tweet 6 — Persistence**

> The non-obvious win:
>
> Sessions live on the managed VPS, not the laptop. Lid closed, on a plane, on
> a different machine — they keep running.
>
> The morning ritual was "ask Claude what finished overnight," not "set up
> three tmux panes."

*[241 chars]*

---

**Tweet 7 — What Concerto is, plainly**

> Concerto is an MCP server. You point Claude Desktop / Claude Code / any MCP
> client at one URL.
>
> Claude gets 5 tools: start_session, list, get, kill, build.
>
> It orchestrates. You stay in the chat.
>
> Solo $49/mo · Pro $99/mo. Bring your own Claude Pro/Max.

*[273 chars]*

---

**Tweet 8 — CTA + receipts**

> Full StrandedGrid case study with reproducible commands (git log | wc -l, the
> file tree, the Stripe SKU) is in the repo.
>
> If you're a solo dev shipping anything ambitious with Claude Code, this is
> built for you.
>
> 🎼 concerto.run
> 📊 case study + GitHub in replies.

*[277 chars]*

---

## Reply assets (post in the thread after tweet 8)

- **Reply 1:** Link to `concerto.run`
- **Reply 2:** Link to the public GitHub repo for Concerto
- **Reply 3:** Link to the StrandedGrid case study Markdown
  (`https://github.com/ethanadjedj-labs/concerto/blob/main/docs/CASE_STUDY_STRANDEDGRID.md`)
- **Reply 4:** Link to MCP Registry entry once it goes live (per
  [`docs/DISTRIBUTION.md`](../DISTRIBUTION.md))

---

## Posting notes

- This is the "receipts" thread — it's content-dense on purpose. Don't lighten
  the numbers, they're the whole point.
- The 838K LOC number is real but **Claude wrote most of it** — be ready to
  answer "what was actually you vs. Claude" in replies. The honest answer is
  "I did the prompting, the architecture decisions, and the merge decisions;
  Claude wrote the code." Don't bluff.
- If a comment challenges the number with "but 838K lines of generated code
  isn't real engineering": agree partly, then redirect to the **shipped
  product** — Stripe live, 162 basins under surveillance, $800 PDF SKU. The
  output is what matters.
- StrandedGrid's marketing site (strandedgrid.com) is currently 502. Don't
  link it from this thread until it's restored. Link the **case-study doc**,
  which is reproducible from the repo regardless.
- If this thread outperforms variant A, pin it. If not, keep variant A pinned
  and let this one breathe in replies.

---

## Variant D — quote-tweet hook (for amplifying the thread)

> Built a real product (StrandedGrid — $800 PDF on Stripe, 162 basins under
> surveillance, 1,064 commits, 6.5 weeks, solo) using one tool:
>
> Concerto — an MCP server that lets Claude orchestrate parallel Claude Code
> sessions for you.
>
> Receipts ↓

*[268 chars]*
