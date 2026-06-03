// Demo content and timing constants for HeroClaudeDemo.
//
// What this demo shows:
//   The REAL Concerto onboarding wizard at /dashboard/[token] —
//   the 3-step flow a paying customer actually walks through after
//   checkout. Step 1 (Sign in with Claude), Step 2 (Add Concerto as a
//   custom connector in Claude), Step 3 (You're all set + GitHub connect).
//
// Every string below is copied verbatim from
// frontend/app/dashboard/[token]/page.tsx so the demo cannot drift from
// what a logged-in customer actually sees.

export const DEMO_TEXTS = {
  // Wizard progress bar labels
  progressLabels: ["Sign in", "Connect", "Build"] as const,

  // ── Step 1: Sign in to Claude ───────────────────────────────────
  step1: {
    title: "Sign in to Claude",
    blurb:
      "Authorize Concerto with your Claude account so it can run Claude Code on your behalf. Same one-click flow you use to link GitHub.",
    primaryIdle: "Sign in with Claude",
    primaryStarting: "Preparing sign-in…",
    openAnthropic: "Open Anthropic, then click Authorize",
    codeLabel: "Paste the code Anthropic gave you",
    codePlaceholder: "Paste the code here…",
    // The pasted code — same shape Anthropic returns (sk-ant-oat01-…)
    codeTyped: "sk-ant-oat01-•••••••••••••••",
    primaryComplete: "Complete sign-in",
    finishing: "Finishing sign-in…",
    finishingAlt: "Securing your access…",
    helpHint: "The code looks like sk-ant-oat01-… A tab may have opened on its own — if not, use the button above.",
    success: "Signed in. Moving to next step…",
  },

  // ── Step 2: Connect Concerto to Claude ──────────────────────────
  step2: {
    title: "Connect Concerto to Claude",
    blurb:
      "The button opens Claude with everything pre-filled. Just click Add, then Connect — this page jumps ahead the moment you do.",
    primary: "Open Claude & add Concerto",
    instruction: "In Claude: Add · then Connect",
    waiting: "Waiting on Add + Connect in Claude — you'll jump ahead automatically.",
  },

  // ── Step 3: You're all set / Build ──────────────────────────────
  step3: {
    title: "Already have a project? Connect your GitHub.",
    blurb:
      "One click and Claude can build on your existing code right away.",
    githubButton: "Connect your GitHub in one click",
    setHeadline: "You're all set.",
    setBlurb:
      "Concerto is connected. Open Claude, describe what you want built, and Concerto orchestrates the work for you.",
    promptLabel: "JUST SAY, FOR EXAMPLE",
    promptText: "“Build me a Notion-like app”",
    promptHelp:
      "Concerto decides whether it's one focused job or several parallel workstreams — you don't have to think about it.",
    openClaude: "Open Claude",
  },
} as const

// ── Timings (ms from start of loop) ────────────────────────────────
// The loop walks step1 → step2 → step3, then fades out and restarts.
export const DEMO_TIMINGS = {
  // Step 1
  step1AppearAt:        300,
  signInClickAt:      1_600,   // cursor clicks "Sign in with Claude"
  awaitingCodeAt:     2_400,   // card morphs to code-paste form
  codeTypeStartAt:    3_300,   // start typing in paste field
  codeTypeEndAt:      5_300,   // finished typing pasted code
  completeClickAt:    5_900,   // cursor clicks "Complete sign-in"
  finishingAt:        6_100,   // button shows "Finishing sign-in…"
  successAt:          8_000,   // green "Signed in" confirmation
  // Step 2
  step2AppearAt:      9_200,   // progress bar advances, step2 card mounts
  openClaudeClickAt: 10_500,   // cursor clicks "Open Claude & add Concerto"
  waitingAt:         10_700,   // card shows the waiting spinner
  // Step 3
  step3AppearAt:     13_000,   // progress bar advances, step3 card mounts
  githubClickAt:     15_000,   // cursor hovers/clicks "Connect your GitHub"
  // End-of-loop
  fadeOutAt:         17_500,
  loopDuration:      18_800,
  // Typewriter
  streamMs:              26,   // ms per character when typing the code
} as const

export type CursorWaypoint = {
  t: number
  x: number    // 0..1 fraction of container width
  y: number    // 0..1 fraction of container height
  action: "idle" | "move" | "click"
}

// Cursor choreography — coordinates are container-relative fractions so
// the animation scales with the demo on mobile.
export const CURSOR_WAYPOINTS: CursorWaypoint[] = [
  // Start resting just outside the card
  { t:      0, x: 0.78, y: 0.62, action: "idle"  },
  // Move toward "Sign in with Claude" primary button
  { t:  1_000, x: 0.50, y: 0.66, action: "move"  },
  // Click sign-in
  { t:  1_600, x: 0.50, y: 0.66, action: "click" },
  // Move to the paste field after the card morphs
  { t:  2_800, x: 0.48, y: 0.62, action: "move"  },
  // Click the paste field to focus
  { t:  3_200, x: 0.48, y: 0.62, action: "click" },
  // Move down to "Complete sign-in" button after typing
  { t:  5_500, x: 0.50, y: 0.72, action: "move"  },
  // Click complete sign-in
  { t:  5_900, x: 0.50, y: 0.72, action: "click" },
  // Drift right while it finishes
  { t:  7_200, x: 0.66, y: 0.68, action: "idle"  },
  // Wait near the success line
  { t:  8_200, x: 0.55, y: 0.78, action: "move"  },
  // Step 2 mounts — cursor drifts to the new primary button
  { t:  9_800, x: 0.50, y: 0.55, action: "move"  },
  // Click "Open Claude & add Concerto"
  { t: 10_500, x: 0.50, y: 0.55, action: "click" },
  // Drift while the spinner shows
  { t: 11_400, x: 0.62, y: 0.66, action: "idle"  },
  // Step 3 mounts — move to the GitHub button
  { t: 13_700, x: 0.50, y: 0.58, action: "move"  },
  // Hover the GitHub button (no click — we just show it exists)
  { t: 15_000, x: 0.50, y: 0.58, action: "idle"  },
  // Drift down toward the "Open Claude" CTA at the bottom
  { t: 16_200, x: 0.55, y: 0.85, action: "move"  },
  // Pre-fade: gentle rest
  { t: 17_200, x: 0.62, y: 0.82, action: "idle"  },
]
