# Concerto — Product Brief
*Strategic clarity for positioning, persona targeting, and competitive differentiation*
*Version: 2026-05-17 | Phase CONCERTO-LAUNCH*

---

## One-Liner

> **"Claude Code on your cloud — controlled from any browser."** *(9 words)*

**Why this beats the current line** ("Pilot Claude Code workers from your browser. Never open a terminal."):
The current line frames the product negatively ("never open a terminal") and uses "pilot" + "workers" — jargon that obscures the offer. The new line is concrete in both dimensions that matter: *where it runs* (your cloud, not ours) and *how you control it* (any browser, not a terminal). "Your cloud" is the differentiator no competitor can match; it earns the line.

---

## Buyer Personas

### Persona 1 — Maya, the Empowered Product Manager
**Title**: Senior PM at a 30-person Series B startup
**Age / profile**: 32, non-technical, power SaaS user, already pays for Claude Max
**Daily pain**: She has Claude Max but cannot run Claude Code — it requires a terminal she's never opened. Every time she wants a long-running coding task ("refactor all tests to use the new mock factory"), she has to write a spec, hand it to an engineer, wait a day, and review. She's the bottleneck and also the one waiting.
**Current workaround**: Uses Bolt.new for simple prototypes; asks junior engineers to babysit Claude Code sessions on their laptops for bigger tasks. The junior engineers resent it. The output depends on whoever's online.
**What makes her pay $99**: Self-sovereignty. She can provision her own Claude Code environment in five minutes without asking for help. $99 one-time is less than the two engineering hours she burns per ask. The web terminal means she never has to touch a command line. The always-on VPS means she can kick off a job before her standup and check results after.

---

### Persona 2 — Alex, the Solo SaaS Operator
**Title**: Founding engineer / indie hacker running 3 SaaS apps
**Age / profile**: 28, strong developer, Claude Max subscriber, builds everything himself
**Daily pain**: Claude Code runs on his MacBook. When he closes the lid to take a flight, long-running agentic tasks die. He's tried tmux on a rented VPS but the manual setup (install Node, npm install -g @anthropic-ai/claude-code, run `claude auth login` from an SSH session while forwarding a browser auth callback) costs him 90 minutes every time he spins up a new machine. He wants a clean environment per project without the ops overhead.
**Current workaround**: Keeps a spare Hetzner VPS always on, SSH tunnel to it from his laptop for Claude Code sessions. Resets it manually when it gets messy. No web terminal — he uses his laptop to SSH and pray.
**What makes him pay $99**: One payment buys him a clean, pre-configured Claude Code VPS in his own DigitalOcean account — his SSH keys, his data, his billing. He controls it from a browser tab instead of maintaining SSH tunnels. Always-on means his agents work through the night. He can have separate Droplets per project for isolation without fighting a shared environment.

---

### Persona 3 — David, the Technical Founder Under Deadline
**Title**: CTO / technical co-founder of an early-stage startup, 2-person team
**Age / profile**: 35, 10+ years engineering, no time for DevOps, wants leverage not management
**Daily pain**: He wants Claude Code running in parallel on multiple repo contexts simultaneously (frontend, backend, infra). On a local machine this means juggling four terminal windows and praying no session dies. On a remote VPS it means setting up multiple isolated environments manually — a problem he shouldn't be solving given his backlog.
**Current workaround**: Runs Claude Code in local tmux with multiple windows, loses context whenever his battery dies. Occasionally SSHes into a DigitalOcean Droplet he set up by hand, but it took 3 hours to configure and he's afraid to touch it.
**What makes him pay $99**: Instant provisioning of a clean, production-grade Claude Code environment without the 3-hour setup tax. The $99 is less than one hour of his time. The browser terminal makes it accessible to his co-founder (designer, non-engineer) for review. The always-on aspect means he can kick off refactors Friday afternoon and review Saturday morning with everything committed and pushed.

---

## The Actual Job-to-be-Done

**Core JTBD**: *"Help me run Claude Code continuously, from anywhere, on a machine I own — without managing infrastructure myself."*

This has three layers:
1. **Continuity** — the agent keeps running when my laptop closes
2. **Accessibility** — I can check in or redirect from any device without SSH
3. **Ownership** — my data, my cloud account, my billing — not a black box on someone else's server

### Why "Claude Code in a browser" is the right framing

The tempting alternatives, and why they're wrong:

**"Agent platform"** — This suggests you're building orchestration workflows, pipelines, DAGs. Concerto doesn't ask you to define agents. It just runs Claude Code — the tool developers already know. "Platform" adds cognitive overhead; Concerto removes it.

**"Compute orchestrator"** — DevOps language. Repels the PM and indie hacker. Implies Kubernetes, YAML, and a learning curve. The buyer's whole problem is that they don't want to orchestrate compute.

**"AI workforce"** — Science fiction framing that sets expectations it can't meet. Buyers become suspicious and trust drops before the trial starts. The workforce metaphor also implies many agents doing coordinated work; Concerto v1 is one agent per Droplet.

**"Claude Code in a browser"** wins because:
- Claude Code is already validated — the buyer has heard of it, may already use it locally
- "In a browser" exactly describes the access method — not aspirational, just true
- It implicitly resolves the terminal barrier without making that the headline (which reads as defensive)
- It leaves room to grow: multi-agent, parallel Droplets, Hetzner, all fit under this framing naturally

---

## Competitive Differentiation

*All pricing and product claims sourced from competitor websites, verified 2026-05-17.*

### 1. Cursor — cursor.com/pricing
**What they sell**: An AI-native code editor with inline completions, agent requests, cloud agents, and code review. The IDE is the product.
**Who they target**: Active developers who live in an IDE. Cursor replaces VS Code or JetBrains as the primary coding environment.
**Pricing**: Free (Hobby), $20/mo (Individual), $40/user/mo (Teams), Enterprise custom.
**The gap Concerto fills**: Cursor requires a local machine running an IDE. It cannot run headless or from a tablet. Cloud Agents in Cursor run on Cursor's infrastructure, not your cloud account — your code leaves your perimeter. Cursor also requires model credits from Cursor's pool (not your Claude Max subscription). A Claude Max subscriber gets zero leverage from their existing plan when using Cursor.

### 2. Devin — devin.ai/pricing
**What they sell**: A fully autonomous AI software engineer that plans, writes, tests, and deploys code. The pitch is "assign Devin a ticket and walk away."
**Who they target**: Engineering teams who want to delegate entire tasks to an AI agent. Positioned as a junior engineer replacement.
**Pricing**: Free (basic), $20/mo (Pro), $200/mo (Max), $80/mo (Teams), Enterprise custom.
**The gap Concerto fills**: Devin runs on Devin's infrastructure — you never own the environment. At $200/mo for the Max plan, it's 24× more expensive annually than Concerto's $99 one-time. Devin doesn't integrate with your Claude Max subscription. For a user who wants Claude specifically (and already pays for Claude Max), Devin offers a different model family at a higher marginal cost. Devin also has an "autonomous black box" UX — you hand off the task and hope. Concerto keeps you in the driver's seat: you direct, Claude executes.

### 3. Replit Agent — replit.com/pricing
**What they sell**: A browser-based coding environment with integrated AI agents. The IDE and cloud compute are bundled — write, run, and deploy from one tab.
**Who they target**: Beginners, learners, prototypers, and non-developers who want to build apps without any local setup.
**Pricing**: Free (limited credits), $20/mo (Core, up to 2 parallel agents), $95/mo (Pro, up to 10 parallel agents).
**The gap Concerto fills**: Replit's infrastructure is Replit's — you cannot run Replit Agent in your own DigitalOcean account. Replit Agent uses its own model credits, not your Claude Max plan. The $95/mo Pro tier costs more annually than Concerto's $99 one-time after just 2 months. Most critically, Replit Agent is purpose-built for building Replit-hosted apps — it cannot run arbitrary engineering tasks against your existing codebase in your private infrastructure. Concerto runs Claude Code against whatever's in your VPS: any repo, any toolchain.

### 4. Bolt.new — bolt.new/pricing
**What they sell**: Full-stack application generation via conversational AI. "Create stunning apps & websites by chatting with AI." The output is a deployable web app, generated in minutes.
**Who they target**: Product managers, marketers, entrepreneurs, and agencies who want a finished app without writing code. Non-developer first.
**Pricing**: Free (300K tokens/day), $25/mo Pro (10M tokens/mo), $30/member/mo Teams.
**The gap Concerto fills**: Bolt generates apps — it doesn't run a general-purpose coding agent. It cannot: refactor an existing backend, write tests for a repo it didn't create, build a data pipeline, or work on any codebase you didn't start inside Bolt. The output is locked into Bolt's cloud infrastructure. Concerto runs Claude Code against any existing codebase on a machine you own. A Bolt user who graduates to real engineering work has nowhere to go inside Bolt — they need Concerto.

### 5. Lovable — lovable.dev/pricing
**What they sell**: Collaborative, AI-powered web application builder for teams. Real-time collaboration on AI-generated apps with governance features.
**Who they target**: Fast-moving startup teams who want to ship web apps without deep engineering investment. Skews toward non-developers and hybrid teams.
**Pricing**: Free, $25/mo Pro (100 credits), $50/mo Business (100 credits, SSO, team workspaces).
**The gap Concerto fills**: Lovable is a web-app factory — it has a fixed output type (web applications) and runs on Lovable's cloud. Credits run out. The subscription renews monthly. Lovable cannot be directed at arbitrary engineering tasks outside the "build me a web app" paradigm. Like Bolt, it's a finishing tool, not a general-purpose coding agent. And like every other competitor: it doesn't use your Claude Max plan, and it doesn't run in your cloud account.

---

## Three Risks + Mitigations

### Risk 1: Anthropic ships this themselves

**Scenario**: Anthropic adds a "run Claude Code in the cloud" feature to claude.ai — e.g., a managed Claude Code environment bundled with the Max plan. Concerto's core value proposition is eliminated at the platform level.

**Probability**: Medium-high. Anthropic already has the desktop app, IDE extensions, and web interface. Remote execution in a managed environment is a natural next step, likely within 12–18 months.

**Mitigation**:
- **Lean into "your cloud"**: Anthropic will run Claude Code on Anthropic's infrastructure. Concerto runs it on the customer's DigitalOcean account — no vendor lock-in, data stays in the customer's perimeter. Privacy-sensitive users (legal, healthcare, fintech) will pay for this.
- **Expand cloud providers fast**: Ship Hetzner (v2) and AWS/GCP/Azure (v3). Concerto becomes "Claude Code on any cloud" — a multi-cloud provisioner Anthropic won't build.
- **Build the management layer**: Session history, spend tracking per Droplet, multi-project organization, agent scheduling. If Anthropic ships raw remote execution, Concerto differentiates on the control plane.

---

### Risk 2: Customer doesn't have a Claude Max plan

**Scenario**: A buyer sees Concerto, pays $99, and then discovers the product requires a Claude Max subscription ($100/month) that they don't have. Churn and chargebacks follow.

**Probability**: High without explicit pre-purchase messaging. Max plan adoption is growing but nowhere near universal.

**Mitigation**:
- **Pre-qualify in copy**: Make "requires an active Claude Max plan" visible before the Stripe checkout — in the hero section, on the pricing card, and in the FAQ. Not as a disclaimer but as a feature: "Plug your Max plan into a cloud agent."
- **Frame the bundle cost**: "$99 one-time + $100/mo Max + ~$24/mo Droplet = $124/mo all-in for an always-on Claude Code agent." This is still cheaper than Devin Max ($200/mo alone).
- **V2: API key mode**: Accept a raw Anthropic API key (not Max plan) with usage-based billing. Opens the product to the much larger audience of API subscribers. Max plan is the premium path; API key is the accessible path.

---

### Risk 3: Customer abandons after first OAuth

**Scenario**: User pays $99, Droplet provisions successfully, but they get stuck during the Claude Code OAuth step (`claude auth login` in the browser terminal) or when pasting the connector config into claude.ai. Dropout rate at this step could be 30–50% for non-technical users.

**Probability**: High for non-engineer personas (PM, founder without heavy coding background). The OAuth flow requires navigating a callback URL in a browser while the terminal is open — familiar to developers but confusing to others.

**Mitigation**:
- **In-product video guide**: Embed a 90-second screen recording directly in the terminal step UI — showing exactly where to click, what the Claude auth screen looks like, and how to paste the connector config.
- **Email drip**: If the terminal auth hasn't been completed 1 hour after Droplet readiness notification, send a "need help?" email with a step-by-step screenshot guide and a direct link back to the portal.
- **Health-check endpoint**: The portal dashboard should show a live health indicator: "VPS running ✅ | Claude auth ✅ | Connector active ✅". Users can see exactly which step failed and retry without losing context.
- **Idempotent installer**: The cloud-init / installer script must be re-runnable without corruption. If a user's first attempt fails mid-install, they should be able to click "reinstall" in the portal and get a clean environment without provisioning a new Droplet.

---

*End of Product Brief*
