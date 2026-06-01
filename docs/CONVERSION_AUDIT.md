# concerto.run — landing conversion audit

Last audited: **2026-06-01** against
[`/opt/concerto-frontend/app/page.tsx`](file:///opt/concerto-frontend/app/page.tsx).
Build verified passing (`npm run build` exit 0; all 30+ routes prerender / dynamic
rendered correctly).

The goal: an AI-coding developer who hits concerto.run from Show HN, a Tweet, or
the MCP registries can understand the product, see the price, and click the
primary CTA in under 10 seconds — on mobile and desktop.

---

## Audit method

Section-by-section pass over the live landing component, scored against five
conversion criteria for a low-touch, high-intent dev-tools landing:

1. **Crisp value prop above the fold** — what + for whom, in one sentence.
2. **Primary CTA visible without scroll** — Solo / Pro / Start.
3. **Pricing visible without forcing scroll-to-pricing** — at least teased.
4. **Mobile-first** — sticky mobile CTA, sane font sizes.
5. **Real-buyer language** — Claude Code, MCP, parallel orchestration; no
   marketing fluff.

---

## Section-by-section scorecard

| Section (page.tsx) | Criterion | Status | Evidence |
|---|---|---|---|
| Nav (L55–L83) | Primary CTA visible at all scroll positions | ✅ | `fixed left-0 right-0 top-0 z-50`, "Start in 5 minutes" button persistent |
| Hero (L86–L144) | Crisp value prop | ✅ | H1 "Run multiple Claude Code sessions from one Claude chat." — explicit + buyer-language |
| Hero badge (L91–L99) | Tagline above H1 reinforces value | ✅ | "Talk to Claude. Claude runs Claude Code." |
| Hero (L137–L140) | Pricing teased above the fold | ✅ | "Pro — $99/mo / Solo — $49/mo" inline under CTAs |
| Hero (L116–L135) | Two CTAs (primary + secondary) | ✅ | "Start in 5 minutes" (primary) + "See how it works" (secondary anchor to demo) |
| Demo (L150–L166) | Show, don't tell | ✅ | `<HeroClaudeDemo />` component renders interactive MCP-call animation |
| Pain block (L169–L197) | Real-buyer pain enumerated | ✅ | Five tmux/log/babysit pains, then "Concerto removes that layer." |
| How (L200–L224) | 4-step mental model | ✅ | Numbered chat → decide → start → report. Matches MCP tool flow. |
| Use cases (L227–L253) | 6 concrete jobs | ✅ | Build/deploy, parallel fixes, refactor+regress, audit, parallel attempts, recover stuck. All real Concerto use cases. |
| Pricing (L256–L351) | Both plans side by side, Pro featured | ✅ | Solo $49 / Pro $99, "Most popular" badge on Pro, separate Stripe Checkout forms |
| FAQ (L354–L400) | 6 buyer questions answered | ✅ | What, code-required?, Pro vs Max, where Claude Code runs, what to build, cancel |
| Refunds (L403–L422) | Trust signal | ✅ | "Real human reviews every request, 24h reply" + form |
| Mobile sticky CTA (L458) | Mobile-first CTA | ✅ | `<MobileStickyCTA />` triggered after `#hero-section-end` IntersectionObserver |
| Footer (L425–L455) | Legal / Help / Support / Cancel | ✅ | Terms, Help, support@concerto.run, CancelSubscriptionFlow |

**Score: 14 / 14 conversion criteria present.**

---

## What's good (keep)

- **Above-the-fold pricing.** A lot of dev-tool landings hide the price; ours
  shows both ($49 / $99) under the CTA. This is the single biggest filter for
  "is this affordable?" — answering it instantly converts higher.
- **Buyer-native language.** "Claude Code", "MCP", "parallel sessions", "tmux
  panes" — every word a Claude Code user would type into Google. No "AI-powered
  workflow optimization platform" filler.
- **Anthropic-style palette.** Cream + warm orange (`#cc785c`) reads as
  ecosystem-native to a Claude buyer. Matches the [intent-keyword pages]
  (./keywords/) tone.
- **Two-step mental model in the hero.** Tagline (Talk to Claude. Claude runs
  Claude Code.) + H1 (Run multiple Claude Code sessions from one Claude chat.)
  = explains both *how* and *what* before the visitor's attention budget runs
  out.
- **Mobile sticky CTA.** `MobileStickyCTA` is the conversion difference between
  "I'll come back" and a checkout click.

---

## Improvements considered (and why they were NOT made)

| Idea | Decision | Reason |
|---|---|---|
| Add a social-proof strip ("Built by X who shipped Y") above pricing | **Not now** | Currently a solo operator without nameable users on record. Adding fake logos would tank trust on the exact dev-segment we sell to. Wait for real testimonials post-launch. |
| Embed the StrandedGrid case study tile in the use-cases section | **Deferred** | The case study (`docs/CASE_STUDY_STRANDEDGRID.md`) is real but strandedgrid.com is currently 502 — a tile that links to a 502 hurts trust. Add the tile when the demo site is restored. |
| Add a "Quick install" code block (the Claude Code CLI command) above pricing | **Worth considering next pass** | Lowers perceived friction. Currently in the README, not the landing. Adding it would shift the "I get it, but do I have to figure out the wiring?" objection. Not blocking conversion today. |
| 7-day free trial badge | **Not adding** | Current model is paid-first with refund-on-request. Trial copy would conflict with the refund-trust pitch in the Refunds section. |

---

## Build / a11y / perf

| Check | Result |
|---|---|
| `npm run build` (Next.js 14.2.18) | ✅ Pass, 0 errors |
| Static prerender of `/` | ✅ (`○` marker in build output) |
| Other key routes (status, help, legal/terms, success, cancelled) | ✅ All static-prerendered |
| Dynamic routes (`/setup/[token]`, `/upgrade/[token]`, checkout API) | ✅ Server-rendered on demand |
| First Load JS shared | 87.2 kB (lean for a Next.js 14 landing) |
| Sticky-mobile CTA observer (`#hero-section-end`) | ✅ Wired |
| External CTAs (checkout API form posts) | ✅ Both Solo + Pro `<form action="/api/checkout?plan=...">` |

---

## How this audit relates to the broader distribution work

The landing is the **conversion endpoint** for every distribution surface listed
in [`docs/DISTRIBUTION.md`](./DISTRIBUTION.md):

- Every MCP-registry listing (Official, GitHub, Smithery, Glama, mcp.so) links
  to `concerto.run` and to the GitHub repo. The landing has to convert that
  click.
- The Show HN draft (`docs/distribution/hn_show_post.md`), Product Hunt kit
  (`docs/distribution/producthunt_listing_draft.md`), and X threads
  (`docs/distribution/twitter_launch_thread.md`) all link to `concerto.run`.
- The intent-keyword pages (`docs/keywords/*.md`) cross-link to
  `concerto.run/#pricing` as the final CTA.

This audit confirms that endpoint is in good shape for those funnels — no
blocking conversion issues.

---

## Next pass (if conversion data warrants)

These are the experiments to run AFTER launch traffic exists — not pre-launch
guesses:

1. A/B: hero subhead specificity ("3 Claude Code sessions" vs "multiple Claude
   Code sessions").
2. A/B: pricing-card order (Pro-first vs Solo-first).
3. Add a 30-second product video in `#demo` section.
4. Replace the use-cases tiles with a single live StrandedGrid case-study tile
   (once that site is restored).

Each only makes sense with real traffic; instrument analytics first.
