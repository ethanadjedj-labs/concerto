# Maestro FAQ

---

### 1. What is Maestro?

Maestro provisions a DigitalOcean Droplet inside your own DO account, installs Claude Code on it, and wires it to your claude.ai conversations via an MCP connector. After a ~3-minute setup, you can give Claude Code tasks in any claude.ai conversation and they run on a real Linux machine — with persistent files, real network access, and no context-window ceiling on tool calls.

---

### 2. Why $99?

The $99 is a one-time setup fee, not a subscription. You pay us once; after that, your only recurring cost is the DigitalOcean Droplet ($12–$24/month, billed by DO directly to your card). We provision, harden, and wire up the machine so you don't have to spend a weekend figuring out cloud-init, MCP, cloudflared, and OAuth flows.

---

### 3. Do I need Claude Max?

Claude Max ($100/month) gives you the highest usage limits and access to the most capable models. Maestro works best with Claude Max because long-horizon agentic tasks consume more tokens than light chatting. That said, Maestro itself does not require Max — see the next question.

---

### 4. What if I have Claude Pro instead?

Claude Pro works with the MCP connector, but you'll hit usage limits faster on long agentic tasks. If you're running intensive workloads (full repo audits, multi-hour coding sessions), you'll likely need Max. For lighter use — occasional background tasks, research jobs that complete in < 30 min — Pro is fine.

---

### 5. Can I cancel my Droplet?

Yes. Your Droplet lives in *your* DigitalOcean account. You can destroy it at any time via the DO dashboard. We'll also destroy it on your behalf if you request it via the Maestro dashboard. Destroying the Droplet stops all DigitalOcean charges immediately.

---

### 6. Will I be charged again?

Maestro's $99 is a one-time fee. We do not charge you again unless you provision a second Droplet. Your ongoing cost is the DigitalOcean Droplet (currently $12/month for the default 2 vCPU / 4 GB RAM spec), billed directly by DigitalOcean to whatever card you have on file with them.

---

### 7. What if my DigitalOcean API key is compromised?

1. Immediately revoke the key in the DO dashboard (API → Tokens → Revoke).
2. Generate a new key.
3. Contact **support@maestro.run** — we'll update the stored key and re-verify your Droplet is still under your control.

Your Droplet is in your DO account, so revoking the key prevents us (and anyone else) from making API calls with it. The Droplet itself continues to run; only programmatic management is affected.

---

### 8. Can I use my own SSH key?

Yes. During setup, you can optionally paste your public SSH key. If you do, it's injected into the Droplet and SSH (port 22) is opened in the firewall. If you don't provide a key, SSH is disabled by default — the only access path is the cloudflared tunnel used by the MCP connector. See [SECURITY.md](SECURITY.md) for details.

---

### 9. What is the refund policy?

If provisioning fails (DO API rejection, Droplet boot failure), we offer a full refund automatically — no questions asked. If provisioning succeeds but you change your mind within 48 hours and haven't used the Droplet, email **support@maestro.run** for a full refund. After 48 hours or after first use, refunds are at our discretion. We're a small team and we want to be fair — reach out and we'll work something out.

---

### 10. Won't Anthropic ship this themselves?

Possibly. Anthropic is building operator infrastructure. When and if they do, we'll adapt. In the meantime: Maestro is available today, runs on hardware you own, and doesn't require any Anthropic-side changes. We're not betting against Anthropic — we're filling the gap that exists right now.

---

### 11. Can I run multiple accounts or workspaces?

Not yet. v1 supports one Droplet per customer. Multi-account support (per-conversation credentials, session templates, routing between multiple Droplets) is on the v1.x roadmap. See [ROADMAP.md](ROADMAP.md).

---

### 12. What's on the roadmap?

Short version: Hetzner provider support, multi-account routing, session templates, an observability dashboard, and automatic Claude Code updates in v1.x. Team accounts, SSO, and a managed (no-DO-account-needed) option in v2. See [ROADMAP.md](ROADMAP.md) for dates and details.
