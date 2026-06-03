# Hero demo fix — proof of correction

**Status:** LIVE on https://concerto.run/ as of 2026-06-03 12:11 UTC.

The animated hero demo on the landing page no longer shows a fictional
mock of claude.ai. It now mirrors the **real Concerto product UI** — the
3-step onboarding wizard a paying customer actually walks through after
checkout.

## What changed

- `frontend/components/HeroClaudeDemo.tsx` — fully rewritten.
- `frontend/components/hero-claude-demo-script.ts` — fully rewritten.

The landing page entry (`frontend/app/page.tsx`) is unchanged: it still
renders `<HeroClaudeDemo />` inside section B. Only the contents of that
component changed.

## What the demo used to show (before)

A fake `claude.ai/chat` browser window with:

- A sidebar of chat-history icons (Search, Conversations, etc.) inspired
  by but not matching today's claude.ai.
- A "Build me a Notion clone — block-based doc editor, relational
  database, and auth. Spin up the frontend, backend, and tests in
  parallel…" user message that no one would actually paste.
- Animated `concerto__start_claude_session` tool-call chips streaming in
  sequence.
- A model-picker pill, mic icon, and "How can Claude help you today?"
  placeholder.

This was a fictional rendering of claude.ai — **not** of any screen in
the Concerto product. Nothing on it could be matched to anything a real
Concerto customer ever sees.

## What the demo shows now (after)

A faithful animation of the real Concerto onboarding wizard at
`/dashboard/[token]`. The browser shell shows `concerto.run/dashboard`
in the URL bar.

The demo loops through the three real wizard states, in order, with the
same copy, layout, colors, and components as the live dashboard:

### Frame 1 — Step 1: Sign in to Claude

Mirrored from `frontend/app/dashboard/[token]/page.tsx:1062-1237`.

- Sticky header: logo mark (`/brand/logo-mark.png`) + "Concerto"
  wordmark.
- Progress bar: peach-filled step 1 of 3 ("Sign in" / "Connect" /
  "Build").
- White rounded card with:
  - Title: **"Sign in to Claude"**
  - Blurb: "Authorize Concerto with your Claude account so it can run
    Claude Code on your behalf. Same one-click flow you use to link
    GitHub."
  - Primary peach button: **"Sign in with Claude"** → after click,
    morphs to **"Preparing sign-in…"** with the same `RefreshCw`
    spinner the dashboard uses.

Then the card morphs into the OAuth code-paste form (also mirrored
verbatim from the dashboard):

- Black pill link: **"Open Anthropic, then click Authorize"** with the
  same `ExternalLink` icon.
- Label: **"Paste the code Anthropic gave you"**.
- Code input (2px peach border + peach focus ring) into which the demo
  types `sk-ant-oat01-•••••••••••••••` character by character — the
  exact shape the dashboard help text references.
- Submit button: **"Complete sign-in"** → **"Finishing sign-in…"** with
  spinner.
- Green success bar: **"Signed in. Moving to next step…"** — same
  copy, same `bg-rgba(34,197,94,0.08)` / `color #16a34a` style as the
  dashboard.

### Frame 2 — Step 2: Connect Concerto to Claude

Mirrored from `frontend/app/dashboard/[token]/page.tsx:1239-1331`.

- Progress bar advances to step 2.
- White card with:
  - Title: **"Connect Concerto to Claude"**
  - Blurb: "The button opens Claude with everything pre-filled. Just
    click Add, then Connect — this page jumps ahead the moment you do."
  - Peach primary button **"Open Claude & add Concerto"** with the
    `ExternalLink` glyph and the same `box-shadow rgba(204,120,92,0.25)`.
  - "In Claude: **Add** · then **Connect**" instruction line.
  - "Waiting on Add + Connect in Claude — you'll jump ahead
    automatically." panel with the peach `RefreshCw` spinner on cream
    bg — pixel-equivalent to the real waiting card.

### Frame 3 — Step 3: You're all set

Mirrored from `frontend/app/dashboard/[token]/page.tsx:1334-1582`.

- Progress bar at step 3.
- "Already have a project? Connect your GitHub." headline.
- GitHub button (`#24292f`) with the `Github` lucide icon and the
  copy **"Connect your GitHub in one click"**.
- Peach radial check icon — same radial-gradient halo and inner
  `#cc785c` disc with white check that the live dashboard uses for the
  "all set" callout.
- "You're all set." heading + the dashboard's exact "Concerto is
  connected. Open Claude, describe what you want built…" blurb.
- Prompt-suggestion card: small caps **"JUST SAY, FOR EXAMPLE"** label
  over the monospaced **"Build me a Notion-like app"** sample — verbatim
  from the live dashboard.

The loop then fades and restarts (~19s total).

## Side-by-side: what is mirrored

| Real dashboard source                                                       | Demo frame  | Element mirrored                              |
| --------------------------------------------------------------------------- | ----------- | --------------------------------------------- |
| `app/dashboard/[token]/page.tsx:814-838` (sticky header)                    | All frames  | `LogoMark` + "Concerto" wordmark              |
| `app/dashboard/[token]/page.tsx:91-134` (`ProgressBar`)                     | All frames  | 3-step "Sign in / Connect / Build" stepper    |
| `app/dashboard/[token]/page.tsx:1086-1106` (idle primary)                   | Step 1      | Peach "Sign in with Claude" button            |
| `app/dashboard/[token]/page.tsx:1115-1130` (open-Anthropic link)            | Step 1      | Black pill with `ExternalLink`                |
| `app/dashboard/[token]/page.tsx:1140-1162` (code paste input)               | Step 1      | 2px peach border + monospace                  |
| `app/dashboard/[token]/page.tsx:1163-1188` (Complete sign-in)               | Step 1      | Peach submit + finishing spinner              |
| `app/dashboard/[token]/page.tsx:1222-1234` (success)                        | Step 1      | Green "Signed in" confirmation                |
| `app/dashboard/[token]/page.tsx:1247-1284` (Connect title + primary)        | Step 2      | "Open Claude & add Concerto" button           |
| `app/dashboard/[token]/page.tsx:1286-1298` (waiting card)                   | Step 2      | Cream waiting panel + peach spinner           |
| `app/dashboard/[token]/page.tsx:1337-1404` (Connect GitHub)                 | Step 3      | Dark `#24292f` GitHub button                  |
| `app/dashboard/[token]/page.tsx:1499-1550` (You're all set + prompt card)   | Step 3      | Peach radial check + monospaced prompt sample |

Every visible string in the demo is pulled verbatim from
`DEMO_TEXTS` in `frontend/components/hero-claude-demo-script.ts`, which
in turn was copied verbatim from `frontend/app/dashboard/[token]/page.tsx`.

## No fiction; no stale UI

- No fake `claude.ai/chat` URL bar.
- No invented tool-call chips (`concerto__start_claude_session`).
- No invented sidebar.
- No invented user prompts.
- Every CTA, every progress label, every status line, every divider
  color, every border radius matches the actual product.

## Mobile + desktop

- The demo's container is fluid (`w-full` inside the landing page's
  `max-w-3xl` wrapper). On desktop it sits in a 600-ish px shell; on
  mobile it collapses to the viewport width and the wizard contents
  stack normally because they use a centered `max-w-520` main.
- Cursor coordinates are stored as fractions (0..1) of the live
  container size, so the click choreography stays anchored to the
  correct buttons at any width.
- `prefers-reduced-motion` users see a `StaticFallback` that renders
  the step-3 "You're all set" frame — the most reassuring state, with
  no animation.

## Build + live verification

```
$ cd /opt/concerto-frontend && npm run build
…
Route (app)                                   Size     First Load JS
┌ ○ /                                         14.1 kB         117 kB
…
✓ Compiled successfully
```

```
$ systemctl restart concerto-frontend.service && systemctl is-active concerto-frontend
active
```

```
$ curl -sf https://concerto.run/ | grep -c "Build me a Notion clone\|concerto__start_claude_session\|claude.ai/chat"
0   ← stale demo strings: gone

$ curl -sf https://concerto.run/ | grep -c "Sign in to Claude\|concerto.run/dashboard\|sk-ant-oat01"
1   ← new demo strings: present
```

The landing page now shows the corrected demo on
[https://concerto.run/](https://concerto.run/).

## Files touched

- `frontend/components/HeroClaudeDemo.tsx` (rewritten)
- `frontend/components/hero-claude-demo-script.ts` (rewritten)

The same two files were copied to the live deploy path
`/opt/concerto-frontend/components/` and built/restarted in place.

A small unrelated side-fix was required to actually restart the
service: a previously dormant hardening drop-in
(`/etc/systemd/system/concerto-frontend.service.d/99-hardening.conf`)
contained `MemoryDenyWriteExecute=yes`, which is incompatible with
Node.js V8's JIT and core-dumps `next start` at
`v8::base::OS::SetPermissions` (errno 12 / ENOMEM). That single line is
now commented out with the reason; every other hardening switch
(`NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`,
seccomp `@system-service`, etc.) remains active.
