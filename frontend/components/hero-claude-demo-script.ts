// Demo content and timing constants — edit this file to change what the demo shows.
// Animation script: 18s loop demonstrating parallel Claude Code sessions via Concerto MCP.

// ── VARIANT SELECTOR ────────────────────────────────────────────────────────
// Switch the active variant by changing this import alias:
//   "VARIANT_A" = default (balanced, natural cursor movement)
//   "VARIANT_B" = calm/slow (fewer cursor hops, longer pauses, meditative pace)
//   "VARIANT_C" = snappy (fast cursor, tight timing, high-energy)
//
// To switch: change `export const DEMO_TIMINGS = VARIANT_A.timings` etc. at bottom.
// ─────────────────────────────────────────────────────────────────────────────

export const DEMO_TEXTS = {
  userMessage:
    "Build me a Notion clone - block-based doc editor, relational database, and auth. Spin up the frontend, backend, and tests in parallel, watch them, and tell me when it's ready.",
  assistantProse1:
    "On it. I'm spawning three Claude Code sessions - one for the block editor, one for the backend + database, one for tests. Starting now.",
  assistantProse2: "All three running. I'm watching their progress.",
  assistantProse3:
    "Editor and backend are done. Tests pass - your Notion clone is live. Want me to add doc sharing, or deploy it to your domain?",
}

// ── VARIANT A — Balanced (DEFAULT) ──────────────────────────────────────────
// Natural, unhurried cursor movement. Mimics a real user who types, sends, then
// watches Claude work. Best for most audiences.
const VARIANT_A_TIMINGS = {
  userMessageAt:    0,
  prose1At:         1_000,
  chip1At:          4_000,
  chip2At:          6_000,
  chip1CompleteAt:  9_000,
  chip2CompleteAt: 10_000,
  prose2At:        11_000,
  chip3At:         13_000,
  chip3CompleteAt: 14_500,
  prose3At:        15_000,
  fadeOutAt:       17_000,
  loopDuration:    18_000,
  streamMs:            10,
}

// Cursor waypoints for VARIANT A.
// Each entry: { t: ms, x: 0-1 (fraction of component width), y: 0-1 (fraction of height), action? }
// x/y are fractional so the component can scale them to actual px.
// actions: "click" | "idle" | "move"
const VARIANT_A_CURSOR = [
  // Start: cursor resting near bottom-right (near send button)
  { t:     0, x: 0.82, y: 0.87, action: "idle"  as const },
  // T=0ms: user clicks send — cursor on send button, click
  { t:   200, x: 0.82, y: 0.87, action: "click" as const },
  // Cursor drifts up-right after sending, natural post-click drift
  { t:   700, x: 0.75, y: 0.70, action: "move"  as const },
  // Moves toward message area to "read" response
  { t: 1_500, x: 0.60, y: 0.42, action: "move"  as const },
  // Settles while prose streams
  { t: 3_000, x: 0.55, y: 0.50, action: "idle"  as const },
  // Chip 1 appears — cursor moves toward it
  { t: 4_200, x: 0.50, y: 0.58, action: "move"  as const },
  // Chip 2 appears — cursor moves slightly down (parallel wow)
  { t: 6_200, x: 0.50, y: 0.64, action: "move"  as const },
  // Cursor drifts away while chips process — natural "watching" position
  { t: 7_500, x: 0.62, y: 0.55, action: "idle"  as const },
  // Chips complete — cursor moves to follow prose 2
  { t:11_200, x: 0.55, y: 0.68, action: "move"  as const },
  // Chip 3 active — cursor tracks it
  { t:13_200, x: 0.50, y: 0.74, action: "move"  as const },
  // Chip 3 complete — cursor begins drifting toward input
  { t:14_800, x: 0.65, y: 0.80, action: "move"  as const },
  // Final prose — cursor settles near input area
  { t:16_000, x: 0.78, y: 0.88, action: "idle"  as const },
  // Pre-fade: cursor moves to send, ready for next loop
  { t:16_800, x: 0.82, y: 0.87, action: "move"  as const },
]

// ── VARIANT B — Calm / Slow ──────────────────────────────────────────────────
// Fewer cursor hops. Cursor stays mostly still, moves only when necessary.
// Good for audiences who find movement distracting. Pace feels meditative.
// Switch: export DEMO_TIMINGS = VARIANT_B_TIMINGS, CURSOR_WAYPOINTS = VARIANT_B_CURSOR
const VARIANT_B_TIMINGS = {
  userMessageAt:    0,
  prose1At:         1_500,
  chip1At:          5_000,
  chip2At:          7_500,
  chip1CompleteAt: 10_500,
  chip2CompleteAt: 11_500,
  prose2At:        12_500,
  chip3At:         15_000,
  chip3CompleteAt: 16_500,
  prose3At:        17_000,
  fadeOutAt:       20_000,
  loopDuration:    21_000,
  streamMs:            14,  // slower streaming — feels more considered
}

const VARIANT_B_CURSOR = [
  { t:     0, x: 0.80, y: 0.88, action: "idle"  as const },
  { t:   300, x: 0.82, y: 0.87, action: "click" as const },
  { t: 1_200, x: 0.65, y: 0.60, action: "move"  as const },
  // Stays put for a long time — unhurried
  { t: 5_500, x: 0.52, y: 0.62, action: "move"  as const },
  { t:10_000, x: 0.52, y: 0.62, action: "idle"  as const },
  { t:15_200, x: 0.52, y: 0.72, action: "move"  as const },
  { t:19_000, x: 0.80, y: 0.88, action: "move"  as const },
]

// ── VARIANT C — Snappy / High-energy ────────────────────────────────────────
// Fast cursor, tight timing. More cursor activity. Feels like an impatient
// power user who types fast and tracks every action.
// Switch: export DEMO_TIMINGS = VARIANT_C_TIMINGS, CURSOR_WAYPOINTS = VARIANT_C_CURSOR
const VARIANT_C_TIMINGS = {
  userMessageAt:    0,
  prose1At:           700,
  chip1At:          3_000,
  chip2At:          4_500,
  chip1CompleteAt:  7_500,
  chip2CompleteAt:  8_200,
  prose2At:         8_800,
  chip3At:         10_500,
  chip3CompleteAt: 11_500,
  prose3At:        12_000,
  fadeOutAt:       14_000,
  loopDuration:    15_000,
  streamMs:             8,  // snappier streaming
}

const VARIANT_C_CURSOR = [
  { t:    0,  x: 0.82, y: 0.87, action: "idle"  as const },
  { t:  100,  x: 0.82, y: 0.87, action: "click" as const },
  { t:  400,  x: 0.60, y: 0.40, action: "move"  as const },
  { t: 3_100, x: 0.50, y: 0.55, action: "move"  as const },
  { t: 4_600, x: 0.50, y: 0.60, action: "move"  as const },
  { t: 7_600, x: 0.60, y: 0.52, action: "move"  as const },
  { t: 8_900, x: 0.55, y: 0.65, action: "move"  as const },
  { t:10_600, x: 0.52, y: 0.70, action: "move"  as const },
  { t:11_600, x: 0.68, y: 0.80, action: "move"  as const },
  { t:13_500, x: 0.82, y: 0.87, action: "move"  as const },
]

// ── ACTIVE VARIANT (change here to switch) ───────────────────────────────────
export const DEMO_TIMINGS = VARIANT_A_TIMINGS
export const CURSOR_WAYPOINTS = VARIANT_A_CURSOR

// Type export for the component
export type CursorWaypoint = (typeof VARIANT_A_CURSOR)[number]
