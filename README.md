# Maestro — Remote Workshop for Claude Code Agents

**One payment. One API key. Your Claude Code agent runs on a dedicated cloud machine, 24/7.**

Maestro provisions a DigitalOcean Droplet inside *your* DO account, installs Claude Code + an MCP server + a cloudflared tunnel, and hands you a connector you paste into claude.ai. From that moment, any conversation you start can reach a full Linux environment with persistent state, real network access, and no token-limit on tool calls.

---

## Why Maestro

- **Founders** — ship without spinning up dev infra. Claude Code handles it.
- **Consultants** — run long-horizon research, audits, and refactors while you sleep.
- **Power developers** — give Claude a real machine; stop babysitting context windows.

## 1-Minute Tour

```
1. Pay $99 at maestro.run
2. Enter your DigitalOcean API key
3. Backend provisions your droplet (< 3 min)
4. An embedded terminal pops up — complete Claude OAuth (30 s)
5. Copy the connector config that appears
6. In any claude.ai conversation → paste the config → ✓
```

From that point, Claude Code runs on your Droplet. Files persist. Processes persist. You close the browser and it keeps going.

## How It Works

```
claude.ai ──MCP─► cloudflared tunnel ──► ttyd/MCP server (your Droplet)
                                                │
                               Claude Code + your code + any tool
```

1. **Payment** — Stripe processes $99 (one-time). We fire a webhook.
2. **Provisioning** — Our FastAPI backend calls the DO API with your key. A Droplet spins up in your account (you own it, you can SSH in).
3. **Install** — `cloud-init` runs the Maestro installer: installs Claude Code, sets up an MCP server, starts a cloudflared tunnel, locks the system so only the tunnel reaches the machine.
4. **OAuth** — An embedded web terminal (ttyd, tunnel-only) lets you run `claude` once to authenticate with Anthropic.
5. **Connect** — We display the MCP connector JSON. Paste it into claude.ai → Settings → Connectors.
6. **Work** — Open any conversation. Claude Code tools are live.

## Setup in 5 Minutes

### Prerequisites

- A [DigitalOcean](https://cloud.digitalocean.com/) account with billing enabled
- A [Claude Max](https://claude.ai) subscription (or Claude Pro — see FAQ)
- $99

### Steps

1. Go to **[maestro.run](https://maestro.run)** and click **Get Started**.
2. Complete the Stripe checkout.
3. On the setup page, paste your **DigitalOcean API key** (Personal Access Token, write scope).
4. Wait ~2-3 minutes while we provision your Droplet.
5. In the embedded terminal, run `claude` and complete the Anthropic OAuth flow.
6. Copy the connector config and paste it in **claude.ai → Settings → Connectors**.
7. Start a conversation. Claude Code is live.

Need help? Join the [Discord community](https://discord.gg/maestro) — real humans, fast replies.

## Repo Structure

```
frontend/   — Next.js customer portal (payment, onboarding, dashboard)
backend/    — FastAPI provisioning service (Stripe webhooks, DO API, sessions)
installer/  — Bash installer delivered via install.maestro.run (cloud-init)
docs/       — Architecture, security, FAQ, custom style, roadmap
emails/     — Transactional email templates (Resend)
```

## Docs

- [Architecture](docs/ARCHITECTURE.md) — system diagram, components, latency budget
- [Security](docs/SECURITY.md) — data handling, encryption, GDPR posture
- [FAQ](docs/FAQ.md) — 12 questions answered
- [Custom Style](docs/CUSTOM_STYLE.md) — paste into claude.ai for the operator experience
- [Roadmap](docs/ROADMAP.md) — what's coming in v1.x and v2

## License

MIT — see [LICENSE](LICENSE).
