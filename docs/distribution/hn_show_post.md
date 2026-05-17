# Show HN: Concerto

**Titre** : Show HN: Concerto – one-click Claude Code workspace, hosted ($39/mo) or BYOC in your own cloud ($99 one-time)

---

**Body** :

I built Concerto to solve a specific problem I kept running into: I wanted Claude Code running persistently on a cloud server — not tied to my laptop — and accessible from any browser without managing SSH configs. Setting it up manually every time is tedious. I wanted a single purchase that handled everything.

**Two plans**: Hosted ($39/mo, Concerto manages the infrastructure) or BYOC ($99 one-time, deploys into your own DigitalOcean account). Both give you the same browser terminal + MCP connector. The BYOC path: enter your DigitalOcean API key and Concerto provisions an Ubuntu 24.04 Droplet (2 vCPU / 4 GB RAM) in your own account. A cloud-init script installs Claude Code via npm, starts a ttyd terminal server behind a cloudflared tunnel, and pings back when ready. The browser opens an xterm.js terminal where you run `claude auth login` (standard OAuth flow, Concerto never sees your Anthropic credentials). You then paste an MCP connector snippet into claude.ai and your agent is live.

**Tech stack**:
- Provisioner: FastAPI + DigitalOcean API, cloud-init for Droplet bootstrap
- Terminal: ttyd listening on loopback, exposed via cloudflared quick tunnel, proxied through the backend as a single `wss://api.concerto.run/terminal/<token>` endpoint — browser connects there, no CORS complexity
- MCP: standard MCP server running on the Droplet alongside Claude Code
- Auth: Claude OAuth — Concerto's backend only stores the session token and ttyd credential; Anthropic auth happens entirely in your browser against Anthropic's servers

**What works today**: end-to-end provisioning, cloud-init bootstrap, browser terminal (WebSocket with the `tty` subprotocol that ttyd requires — silent failure if you forget it), MCP connector generation, Stripe payment flow.

**What doesn't work yet**: multi-Droplet support (parallel agents), SSH key rotation UI, automatic Droplet resizing. The provisioner installs Claude Code but you still need a Claude Max plan — Concerto doesn't bundle or proxy Anthropic API credits.

**Why these prices**: Hosted ($39/mo) is all-in — Concerto handles compute, maintenance, uptime. BYOC ($99 one-time) covers the provisioning automation only; ongoing compute is ~$24/mo billed directly by DigitalOcean to your account. No Concerto subscription on BYOC, no markup on compute.

**One thing I'm genuinely unsure about**: whether the BYOC "runs in your cloud, not ours" angle is a meaningful differentiator to most users, or whether the fully managed Hosted plan is what people actually want — they just didn't have it as an option before. Curious what this community thinks, especially people who've run Claude Code on remote servers before.

concerto.run — feedback welcome, including the harsh kind.
