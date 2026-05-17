---
title: "Concerto — your Claude Code agent, always on"
geometry: margin=2cm
fontsize: 11pt
---

# Concerto

**You're the soloist. Concerto gives you the orchestra.**

A Claude Code agent that runs in your cloud, ready from any browser, any device — without touching a terminal.

---

## How it works

1. **Choose your plan** — Hosted ($39/mo, fully managed) or BYOC ($99 one-time, deploy into your own DigitalOcean account).
2. **Automatic setup** — Concerto provisions an Ubuntu 24.04 server (2 vCPU / 4 GB RAM), installs Claude Code via npm, sets up a cloudflared tunnel, and opens a browser terminal. Takes 3–5 minutes.
3. **Connect** — complete Claude OAuth in the browser, paste the MCP connector snippet into claude.ai. Your agent is live.

---

## Who it's for

- **Claude Max subscribers** who want an always-on agent without managing infrastructure
- **Developers working across devices** who don't want to maintain SSH configs on every machine
- **Operators** running long-horizon Claude Code tasks who need a stable, persistent environment

---

## Pricing

| | **Hosted** ★ | **BYOC** |
|---|---|---|
| Price | $39/month | $99 one-time |
| Infrastructure | Managed by Concerto | Your DigitalOcean account |
| Compute cost | Included | ~$24/mo billed by DigitalOcean |
| Data ownership | Your files, isolated environment | Your VPS, your account |

No hidden fees. No markup on compute. Concerto has no persistent access to your environment after provisioning.

---

**concerto.run**
