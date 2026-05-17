# Reddit — r/selfhosted

**Titre** : Concerto: self-hosted Claude Code on your own DigitalOcean Droplet — browser terminal, MCP connector, $99 one-time (or $39/mo hosted)

---

**Body** :

Built this because I wanted Claude Code running on my own infrastructure, not someone else's managed platform, and accessible from any browser without maintaining SSH configs across machines.

**What Concerto does**: you enter your DigitalOcean API key, it provisions a Droplet in your account (Ubuntu 24.04, 2 vCPU / 4 GB RAM), runs a cloud-init script that installs Claude Code (npm), starts ttyd for the browser terminal, and brings up a cloudflared tunnel. You get a browser terminal to complete Claude OAuth. Then a ready-to-paste MCP connector snippet for claude.ai. Whole provisioning takes 3–5 minutes.

**The self-hosted angle**: the Droplet runs in your DigitalOcean account. You own the VPS, you own the data, you control the keys. Concerto's backend handles the initial provisioning and proxies the WebSocket terminal connection but has no persistent access to your Droplet after setup. Your SSH public key is injected during cloud-init so you can also SSH in directly if you prefer.

**Pricing**: BYOC plan (this sub's crowd) is $99 one-time — covers the provisioning automation; ongoing compute is ~$24/mo directly to DigitalOcean. There's also a Hosted plan at $39/mo if you'd rather not manage the Droplet at all.

**Honest caveats**:
- You still need a Claude Max plan ($100/mo from Anthropic) — Concerto doesn't bundle API access or credits
- v1 is one Droplet per account; if you want parallel agents you'd provision additional Droplets manually for now
- BYOC: $99 is for the provisioning automation; ongoing compute is ~$24/mo directly to DigitalOcean
- Hosted: $39/mo all-in, Concerto manages the infrastructure

**Tech details** (for the people who want them):
- ttyd behind cloudflared quick tunnel — WebSocket subprotocol `tty` is required or the connection silently receives no data (fun debugging session)
- The backend proxies the WS so the browser talks to a single `wss://` endpoint, avoiding cross-origin issues
- cloud-init writes a systemd unit for ttyd with `--credential concerto:<session_token>` — no open root shells
- Provisioner is FastAPI on a VPS behind Cloudflare tunnel; SQLite for session state

If you're already running Claude Code manually on a remote box and want a repeatable, browser-accessible setup without rebuilding it on every new machine — this might save you a few hours of config. If you want full control over every config detail from day one, you'd probably prefer doing it yourself.

Happy to share the cloud-init template or answer questions about the ttyd/cloudflared setup — that part had some non-obvious failure modes worth documenting.

concerto.run
