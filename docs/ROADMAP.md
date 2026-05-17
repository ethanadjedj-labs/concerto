# Concerto Roadmap

## v1.0 — Shipped (May 2026)

- DigitalOcean provider
- One-time $99 provisioning (Stripe)
- cloud-init installer (Claude Code + MCP relay + cloudflared + ttyd)
- claude.ai MCP connector
- Transactional email flow (confirmation, ready, failure, welcome)
- Setup dashboard + embedded OAuth terminal

---

## v1.x — In Progress / Planned

| Feature | Target | Notes |
|---------|--------|-------|
| **Hetzner provider support** | Q3 2026 | Hetzner is ~40% cheaper per vCPU than DO; popular with EU customers. Same installer, new provider adapter in the backend. |
| **Multi-account routing** | Q3 2026 | Per-conversation credentials: link multiple Droplets to one claude.ai account and route by conversation tag or connector alias. |
| **Session templates library** | Q3 2026 | Pre-configured environments (Python dev, Node dev, data science, Rust) installable in one click after provisioning. |
| **Observability dashboard** | Q4 2026 | Per-session metrics: tool calls/min, active processes, disk usage, uptime. Accessible from the Concerto web dashboard. |
| **Automatic Claude Code updates** | Q4 2026 | Droplet pulls the latest Claude Code release automatically; dashboard shows current version and last update time. |
| **Usage alerts** | Q4 2026 | Email notification when a session has been idle for > 24 h or when DO billing estimate exceeds a threshold. |

---

## v2 — 2027

| Feature | Notes |
|---------|-------|
| **Managed offering** | No DO account required. We provision and manage the Droplet; customers pay a flat monthly rate. Target: non-technical power users. |
| **Team accounts** | Shared Droplet pool per team, role-based access, usage attribution per member. |
| **SSO** | Google Workspace and Okta SAML for team plans. |
| **Multi-region** | Automatic Droplet placement by customer geography. |
| **Connector marketplace** | One-click install of additional MCP tools (browser, PDF, database connectors) alongside the Concerto base install. |

---

## Not Planned (Yet)

- Windows or macOS VMs — Linux-only for now; the installer complexity would multiply.
- In-browser IDE — claude.ai is the IDE. Concerto is the backend, not a competing frontend.
- Support for Anthropic competitors — Concerto is built around Claude Code specifically.

---

*Roadmap items are targets, not commitments. Email support@concerto.run to share feedback or vote on priorities.*
