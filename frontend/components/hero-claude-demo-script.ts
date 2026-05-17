// Demo content and timing constants — edit this file to change what the demo shows.
// Animation script: 18s loop demonstrating parallel Claude Code sessions via Concerto MCP.

export const DEMO_TEXTS = {
  userMessage:
    "Build me a small website to track my freelance invoices.",
  assistantProse1:
    "I'll set this up. Let me spawn a session on your remote machine — it'll handle the project setup and build out the pages.",
  assistantProse2: "Both sessions running. I'll check progress in a moment.",
  assistantProse3:
    "The invoice tracker is ready. You can add clients, log invoices, mark them paid. Want me to add anything — a monthly summary, payment reminders?",
}

// All timing values in milliseconds, measured from loop start.
export const DEMO_TIMINGS = {
  // T=0s: user message slides in
  userMessageAt: 0,

  // T=1s: first assistant prose begins streaming word-by-word
  prose1At: 1_000,

  // T=4s: first "Start claude session" chip appears (active, pulsing)
  chip1At: 4_000,

  // T=6s: second chip appears in parallel — the WOW moment
  chip2At: 6_000,

  // T=9s: first chip transitions to complete (checkmark, loader disappears)
  chip1CompleteAt: 9_000,

  // T=10s: second chip completes
  chip2CompleteAt: 10_000,

  // T=11s: assistant follow-up prose
  prose2At: 11_000,

  // T=13s: "Get claude session" chip (brief)
  chip3At: 13_000,

  // T=14.5s: third chip completes
  chip3CompleteAt: 14_500,

  // T=15s: final assistant prose
  prose3At: 15_000,

  // T=17s: fade-out begins
  fadeOutAt: 17_000,

  // T=18s: loop restarts
  loopDuration: 18_000,

  // Character streaming speed (ms per character)
  streamMs: 10,
}
