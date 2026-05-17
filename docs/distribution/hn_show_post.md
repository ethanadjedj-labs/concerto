# Show HN: Maestro

**Titre** : Show HN: Maestro – provision a Claude Code server in your DigitalOcean account from a browser ($99 one-time)

---

**Body** :

I built Maestro to solve a specific problem I kept running into: I wanted Claude Code running persistently on a cloud server — not tied to my laptop — and accessible from any browser without managing SSH configs. Setting it up manually every time is tedious. I wanted a single purchase that handled everything.

**What it does**: you pay $99 once, enter your DigitalOcean API key, and Maestro provisions an Ubuntu 24.04 Droplet (2 vCPU / 4 GB RAM) in your own account. A cloud-init script installs Claude Code via npm, starts a ttyd terminal server behind a cloudflared tunnel, and pings back when ready. The browser opens an xterm.js terminal where you run `claude auth login` (standard OAuth flow, Maestro never sees your Anthropic credentials). You then paste an MCP connector snippet into claude.ai and your agent is live.

**Tech stack**:
- Provisioner: FastAPI + DigitalOcean API, cloud-init for Droplet bootstrap
- Terminal: ttyd listening on loopback, exposed via cloudflared quick tunnel, proxied through the backend as a single `wss://api.maestro.run/terminal/<token>` endpoint — browser connects there, no CORS complexity
- MCP: standard MCP server running on the Droplet alongside Claude Code
- Auth: Claude OAuth — Maestro's backend only stores the session token and ttyd credential; Anthropic auth happens entirely in your browser against Anthropic's servers

**What works today**: end-to-end provisioning, cloud-init bootstrap, browser terminal (WebSocket with the `tty` subprotocol that ttyd requires — silent failure if you forget it), MCP connector generation, Stripe payment flow.

**What doesn't work yet**: multi-Droplet support (parallel agents), SSH key rotation UI, automatic Droplet resizing. The provisioner installs Claude Code but you still need a Claude Max plan — Maestro doesn't bundle or proxy Anthropic API credits.

**Why $99**: one-time covers the provisioning automation. Ongoing compute goes directly to your DO account at standard DO pricing (~$24/mo for a 2 vCPU / 4 GB Droplet). No Maestro subscription, no markup on compute.

**One thing I'm genuinely unsure about**: whether the "runs in your cloud, not ours" angle is a meaningful differentiator to the target user, or whether most people would just prefer a fully managed SaaS where they don't think about the infrastructure at all. Curious what this community thinks — especially people who've run Claude Code on remote servers before.

maestro.run — feedback welcome, including the harsh kind.
