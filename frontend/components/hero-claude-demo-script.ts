// Demo content and timing for HeroClaudeDemo.
//
// What this demo shows:
//   The Concerto product in action — one conversation with Claude triggers
//   parallel Claude Code sessions that do the actual building. The "aha":
//   one chat → N agents coding in parallel → Claude reports back.

export const DEMO_TEXTS = {
  userMessage: "Build me a Notion-like app",

  claudeIntro: "Breaking this into 3 parallel Claude Code sessions via Concerto.",

  sessions: [
    { id: "frontend", label: "frontend", task: "Next.js pages & editor" },
    { id: "backend",  label: "backend",  task: "API + Postgres schema"  },
    { id: "tests",    label: "tests",    task: "unit + integration"     },
  ] as const,

  claudeReport: "All done — pages live, API deployed, 47 tests passing.",
} as const

// ── Timings (ms from start of loop) ────────────────────────────────
export const DEMO_TIMINGS = {
  userTypeStartAt:   500,     // cursor clicks input; typing begins
  userTypeEndAt:    2_200,    // 500 + 27 chars × 63 ms ≈ 2200
  sendClickAt:      2_500,    // cursor moves to Send and clicks
  thinkingAt:       2_700,    // Claude thinking dots appear
  claudeIntroAt:    4_100,    // Claude's "Breaking into…" text replaces dots
  session1At:       4_900,    // first session card fades in
  session2At:       5_700,    // second
  session3At:       6_500,    // third
  session1DoneAt:   8_600,    // first card flips to done
  session2DoneAt:   9_900,    // second
  session3DoneAt:  11_100,    // third
  claudeReportAt:  11_900,    // Claude's final summary appears
  fadeOutAt:       15_000,
  loopDuration:    16_500,
  streamMs:            63,    // ms per typed character
} as const

export type CursorWaypoint = {
  t: number
  x: number    // 0..1 fraction of container width
  y: number    // 0..1 fraction of container height
  action: "idle" | "move" | "click"
}

// Cursor choreography — fractions so the animation scales on mobile.
export const CURSOR_WAYPOINTS: CursorWaypoint[] = [
  // Resting near input, bottom
  { t:      0, x: 0.42, y: 0.90, action: "idle"  },
  // Move to input field
  { t:    380, x: 0.38, y: 0.90, action: "move"  },
  // Click input to focus
  { t:    480, x: 0.38, y: 0.90, action: "click" },
  // Hold while typing
  { t:  2_100, x: 0.38, y: 0.90, action: "idle"  },
  // Move to send button (right of input)
  { t:  2_400, x: 0.88, y: 0.90, action: "move"  },
  // Click send
  { t:  2_500, x: 0.88, y: 0.90, action: "click" },
  // Drift up while Claude thinks
  { t:  3_600, x: 0.68, y: 0.72, action: "idle"  },
  // Move toward session cards
  { t:  5_400, x: 0.52, y: 0.60, action: "move"  },
  // Hover cards area while they run
  { t:  7_200, x: 0.58, y: 0.65, action: "idle"  },
  // Move down to final report
  { t: 11_500, x: 0.50, y: 0.80, action: "move"  },
  // Hover report
  { t: 13_000, x: 0.55, y: 0.82, action: "idle"  },
  // Pre-fade drift
  { t: 14_500, x: 0.62, y: 0.85, action: "idle"  },
]
