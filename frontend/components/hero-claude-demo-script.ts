export interface ResultLine {
  icon: string
  text: string
  delayMs: number
}

export interface HeroDemoScript {
  projectName: string
  existingMessage: string
  userPrompt: string
  claudeResponse: string
  toolName: string
  toolParams: {
    project: string
    prompt: string
    timeout_seconds: number
  }
  resultLines: ResultLine[]
  claudeFollowup: string
  sidebarProjects: Array<{ name: string; active: boolean }>
  sidebarRecents: string[]
  timings: {
    typingStartMs: number
    typingSpeedMs: number
    sentMs: number
    streamingStartMs: number
    streamingSpeedMs: number
    toolLoadingMs: number
    toolExpandedMs: number
    toolResultStartMs: number
    followupMs: number
    loopMs: number
  }
}

export const HERO_SCRIPT: HeroDemoScript = {
  projectName: "ecommerce-api",
  existingMessage:
    "I've reviewed the checkout module. The idempotency_key field exists in the schema but isn't being validated on incoming requests. Let me know what you'd like to tackle next.",
  userPrompt:
    "Refactor the checkout flow to use idempotency keys. Open a PR when tests pass.",
  claudeResponse:
    "I'll spawn a Concerto session to handle this. The agent will inspect the checkout module, add idempotency keys, run tests, and open the PR.",
  toolName: "spawn_claude_code_session",
  toolParams: {
    project: "ecommerce-api",
    prompt:
      "Refactor checkout/ to use idempotency keys per Stripe best practice. Run pytest. Open PR.",
    timeout_seconds: 1800,
  },
  resultLines: [
    { icon: "✓", text: "Session sess_abc123 spawned on droplet-nyc-3", delayMs: 0 },
    { icon: "✓", text: "Reading 4 files in checkout/", delayMs: 350 },
    { icon: "✓", text: "Patched 6 functions with idempotency key support", delayMs: 700 },
    { icon: "✓", text: "Running pytest... 47 tests passed", delayMs: 1100 },
    { icon: "✓", text: "git checkout -b refactor/idempotency-keys", delayMs: 1450 },
    { icon: "✓", text: "Opening PR #142 → ethan/ecommerce-api", delayMs: 1800 },
  ],
  claudeFollowup:
    "Done. PR #142 is open with all 47 tests passing. Took 4 min 12 sec on your VPS. Want me to add a follow-up session to update the API docs?",
  sidebarProjects: [
    { name: "ecommerce-api", active: true },
    { name: "api-docs", active: false },
    { name: "stripe-webhooks", active: false },
  ],
  sidebarRecents: [
    "Add Stripe webhooks",
    "Write project README",
    "Set up CI pipeline",
    "Refactor auth module",
  ],
  timings: {
    typingStartMs: 1000,
    typingSpeedMs: 25,
    sentMs: 3000,
    streamingStartMs: 3500,
    streamingSpeedMs: 9,
    toolLoadingMs: 5100,
    toolExpandedMs: 5900,
    toolResultStartMs: 7000,
    followupMs: 9200,
    loopMs: 12000,
  },
}
