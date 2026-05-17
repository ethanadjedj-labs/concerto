export type Segment =
  | { kind: "text"; content: string }
  | { kind: "tool"; toolName: string; params: Record<string, unknown>; expand: boolean }

export interface ScriptVariant {
  userPrompt: string
  projectName: string
  segments: Segment[]
  sidebarProjects: Array<{ name: string; active: boolean }>
  sidebarRecents: string[]
}

export const HERO_SCRIPTS: ScriptVariant[] = [
  {
    userPrompt:
      "Build me a small website to track my freelance invoices — clients, amounts, paid/unpaid.",
    projectName: "invoice-tracker",
    segments: [
      {
        kind: "text",
        content:
          "I'll set this up on your remote machine. Spawning a session now — it'll create the project, build the pages, and have something running you can click through.",
      },
      {
        kind: "tool",
        toolName: "spawn_claude_code_session",
        params: {
          project: "invoice-tracker",
          prompt: "Build a small invoice tracker with clients, amounts, paid/unpaid status.",
        },
        expand: true,
      },
      {
        kind: "text",
        content: "Session running. Let me check progress.",
      },
      {
        kind: "tool",
        toolName: "get_claude_session",
        params: {},
        expand: false,
      },
      {
        kind: "text",
        content:
          "Good — project is set up, the clients and invoices pages are being built. Should be ready in a minute.",
      },
      {
        kind: "tool",
        toolName: "get_claude_session",
        params: {},
        expand: false,
      },
      {
        kind: "text",
        content:
          "Done. Your invoice tracker is live on your machine. You can add clients, log invoices, mark them paid. Want me to send you the machine URL or add anything else — like a monthly summary view?",
      },
    ],
    sidebarProjects: [
      { name: "invoice-tracker", active: true },
      { name: "freelance-site", active: false },
      { name: "client-portal", active: false },
    ],
    sidebarRecents: [
      "Invoice reminders",
      "Client list import",
      "Payment status",
      "Monthly totals",
    ],
  },
  {
    userPrompt:
      "Help me set up a simple booking page for my photography sessions. Calendar + email confirmation.",
    projectName: "booking-page",
    segments: [
      {
        kind: "text",
        content:
          "I'll set this up on your remote machine. Spawning a session now — it'll build the booking page and wire up email confirmation.",
      },
      {
        kind: "tool",
        toolName: "spawn_claude_code_session",
        params: {
          project: "booking-page",
          prompt:
            "Build a photography session booking page with calendar and email confirmation.",
        },
        expand: true,
      },
      {
        kind: "text",
        content: "Session running. Let me check progress.",
      },
      {
        kind: "tool",
        toolName: "get_claude_session",
        params: {},
        expand: false,
      },
      {
        kind: "text",
        content:
          "Good — the booking page and calendar are being built. Setting up the email confirmation flow too.",
      },
      {
        kind: "tool",
        toolName: "get_claude_session",
        params: {},
        expand: false,
      },
      {
        kind: "text",
        content:
          "Done. Your booking page is live on your machine. Clients can pick a session slot and you'll get an email confirmation. Want me to add anything — like a deposit payment option?",
      },
    ],
    sidebarProjects: [
      { name: "booking-page", active: true },
      { name: "portfolio-site", active: false },
      { name: "client-gallery", active: false },
    ],
    sidebarRecents: [
      "Booking confirmation",
      "Calendar setup",
      "Email templates",
      "Payment deposits",
    ],
  },
  {
    userPrompt: "Create a small dashboard showing my Etsy sales by week with a chart.",
    projectName: "etsy-dashboard",
    segments: [
      {
        kind: "text",
        content:
          "I'll set this up on your remote machine. Spawning a session now — it'll build the dashboard and weekly chart.",
      },
      {
        kind: "tool",
        toolName: "spawn_claude_code_session",
        params: {
          project: "etsy-dashboard",
          prompt: "Build an Etsy sales dashboard with weekly bar chart.",
        },
        expand: true,
      },
      {
        kind: "text",
        content: "Session running. Let me check progress.",
      },
      {
        kind: "tool",
        toolName: "get_claude_session",
        params: {},
        expand: false,
      },
      {
        kind: "text",
        content:
          "Good — the dashboard is being built. The weekly chart layout is done, wiring up the data import now.",
      },
      {
        kind: "tool",
        toolName: "get_claude_session",
        params: {},
        expand: false,
      },
      {
        kind: "text",
        content:
          "Done. Your Etsy dashboard is live on your machine. You'll see weekly sales with a bar chart. Want me to add a date filter or export to CSV?",
      },
    ],
    sidebarProjects: [
      { name: "etsy-dashboard", active: true },
      { name: "product-photos", active: false },
      { name: "shop-analytics", active: false },
    ],
    sidebarRecents: [
      "Weekly sales chart",
      "Product rankings",
      "Revenue trends",
      "Export to CSV",
    ],
  },
]

export const HERO_TIMINGS = {
  typingStartMs: 800,
  typingSpeedMs: 48,
  sentDelayMs: 300,
  streamingSpeedMs: 9,
  afterTextToToolMs: 700,
  toolExpandDelayMs: 600,
  afterTool1Ms: 3000,
  afterTool2Ms: 1000,
  afterTool3Ms: 4000,
  donePauseMs: 2000,
  fadeMs: 700,
  loopMs: 19000,
}
