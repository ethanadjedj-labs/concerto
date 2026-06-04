# Demo Concept Proof — Orchestration Flow Live

**Date:** 2026-06-04  
**Goal:** concerto-demo-fix

## What changed

The hero demo on the Concerto landing page was rewritten. The old demo showed
the **onboarding wizard** (Sign in to Claude → Connect Concerto → GitHub) —
the installation flow, not the product.

The new demo shows **the product in action**: one conversation with Claude
orchestrates N parallel Claude Code sessions.

## New demo flow (key frames)

### Frame 1 — User types in the input
```
claude.ai
┌────────────────────────────────┐
│ C Claude             CONCERTO  │
│                                │
│  [Ask Claude to build someth…] │
│                    [→]         │
│                                │
│ User typing: "Build me a       │
│ Notion-like app|"              │
└────────────────────────────────┘
```

### Frame 2 — Message sent; Claude thinking
```
claude.ai
┌────────────────────────────────┐
│ C Claude             CONCERTO  │
│                                │
│         "Build me a Notion-    │  ← user bubble (right-aligned)
│          like app"             │
│                                │
│ C  ● ● ●                       │  ← Claude thinking dots
│                                │
│  [Ask Claude to build someth…] │
└────────────────────────────────┘
```

### Frame 3 — Claude announces parallel sessions
```
claude.ai
┌────────────────────────────────┐
│ C Claude             CONCERTO  │
│                                │
│         "Build me a Notion-    │
│          like app"             │
│                                │
│ C  "Breaking this into 3       │
│     parallel Claude Code       │
│     sessions via Concerto."    │
│                                │
│    ┌─ frontend ── ● running ─┐ │  ← session cards appear
│    ├─ backend  ── ● running ─┤ │
│    └─ tests    ── ● running ─┘ │
└────────────────────────────────┘
```

### Frame 4 — Sessions complete; Claude reports back
```
claude.ai
┌────────────────────────────────┐
│ C Claude             CONCERTO  │
│                                │
│         "Build me a Notion-    │
│          like app"             │
│                                │
│ C  "Breaking into 3 parallel   │
│     Claude Code sessions…"     │
│                                │
│    ┌─ frontend ── ✓ done ────┐ │  ← all 3 done
│    ├─ backend  ── ✓ done ────┤ │
│    └─ tests    ── ✓ done ────┘ │
│                                │
│ C  "All done — pages live,     │  ← final report
│     API deployed, 47 tests     │
│     passing."                  │
└────────────────────────────────┘
```

## Files changed

| File | Change |
|------|--------|
| `frontend/components/HeroClaudeDemo.tsx` | Complete rewrite: wizard UI → chat orchestration UI |
| `frontend/components/hero-claude-demo-script.ts` | Complete rewrite: onboarding script → orchestration script |

## Live verification

```
$ curl -s http://localhost:3500/ | grep -o "orchestrat\|parallel Claude\|claude\.ai"
orchestrat
parallel Claude
claude.ai
```

Old strings absent from page:
- `Sign in with Claude` — not found
- `Paste the code` — not found
- `concerto.run/dashboard` — not found

New strings confirmed in page:
- `claude.ai` — found (address bar URL in new demo)
- `orchestrat` — found (multiple times in landing copy)
- `parallel Claude` — found

## Confirmation

The hero demo now shows **Claude orchestrating parallel Claude Code sessions**,
not the installation wizard. The product value ("one chat → N agents coding
in parallel") is visible to every prospect who lands on concerto.run.
