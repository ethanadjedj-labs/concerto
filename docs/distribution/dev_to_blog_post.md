# dev.to Blog Post

**Title**: How I built a one-click Claude Code workspace using cloud-init, MCP, and ttyd

**Tags**: `claudecode` `devtools` `cloudcomputing` `tutorial`

**Target length**: 850–950 words

---

## Post

I wanted Claude Code running on a cloud server — accessible from any browser, persistent across sessions, not tied to my laptop. What seemed like a straightforward "spin up a VPS and install stuff" task turned out to have several non-obvious failure modes. This post covers what I built, how it works, and the three places where I lost the most time.

### The goal

A user pays, enters their DigitalOcean API key, and within 5 minutes has:
- A cloud server running Claude Code via npm
- A browser terminal to complete Claude OAuth
- A ready-to-paste MCP connector for claude.ai
- Persistent sessions: close the tab, reopen it, the agent is still there

No SSH configuration on the user's end. No manual installation. One Stripe payment, one API key, done.

### The architecture

The provisioner is a FastAPI service. When a payment is confirmed via Stripe webhook, it calls the DigitalOcean API to create a Droplet:

```python
droplet = do_client.droplets.create(
    name=f"concerto-{token[:8]}",
    region="nyc3",
    size="s-2vcpu-4gb",
    image="ubuntu-24-04-x64",
    user_data=render_cloud_init(session_token=token, ttyd_credential=cred),
    ssh_keys=[operator_ssh_key_id],
    tags=["concerto"],
)
```

The `user_data` field is a cloud-init YAML template. This is where all the real work happens.

### cloud-init: the right way to bootstrap

The cloud-init script needs to run reliably on first boot, in the right order, without a human watching. I use `write_files` to drop configuration and `runcmd` to execute in sequence:

```yaml
write_files:
  - path: /etc/systemd/system/ttyd.service
    content: |
      [Unit]
      Description=ttyd browser terminal
      After=network.target

      [Service]
      ExecStart=/usr/local/bin/ttyd \
        --port 7681 \
        --interface 127.0.0.1 \
        --credential concerto:{{ session_token }} \
        bash
      Restart=always

      [Install]
      WantedBy=multi-user.target

runcmd:
  - apt-get update -qq
  - apt-get install -y -qq nodejs npm curl
  - npm install -g @anthropic-ai/claude-code
  - curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
  - echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared bookworm main' > /etc/apt/sources.list.d/cloudflared.list
  - apt-get update -qq && apt-get install -y cloudflared
  - wget -qO /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64
  - chmod +x /usr/local/bin/ttyd
  - systemctl daemon-reload && systemctl enable --now ttyd
  - cloudflared tunnel --url http://127.0.0.1:7681 --no-autoupdate &
  - curl -s -X POST https://api.concerto.run/internal/droplet-ready -d '{"token":"{{ session_token }}"}'
```

The `droplet-ready` callback is how the provisioner knows the bootstrap finished. The backend then stores the cloudflared tunnel URL, which changes on every boot with quick tunnels (more on this below).

### Failure mode 1: the WebSocket subprotocol

ttyd uses the WebSocket `tty` subprotocol. When I first proxied the WebSocket from the backend to the browser, I forgot to forward the subprotocol header. The connection appeared to succeed — no error, no disconnect — but the browser terminal received exactly zero data. Completely silent.

The fix in FastAPI's WebSocket proxy:

```python
async with websockets.connect(
    upstream_url,
    subprotocols=["tty"],   # without this: silent zero-data connection
    extra_headers={"Authorization": f"Basic {b64cred}"},
) as upstream_ws:
    ...
```

If you're building anything with ttyd and a WebSocket proxy layer, add this before you do anything else.

### Failure mode 2: cloudflared quick tunnels and dynamic URLs

Cloudflare's quick tunnels are great for zero-config HTTPS exposure, but they generate a new random URL every time the tunnel restarts. Since the provisioner needs to store and serve the terminal URL, I needed a reliable way to extract it.

Quick tunnels log the assigned URL to stderr. I capture it with a small wrapper script:

```bash
#!/bin/bash
cloudflared tunnel --url http://127.0.0.1:7681 --no-autoupdate 2>&1 \
  | while read line; do
      echo "$line"
      if echo "$line" | grep -q 'trycloudflare.com'; then
        url=$(echo "$line" | grep -oP 'https://[^\s]+trycloudflare\.com')
        curl -s -X POST https://api.concerto.run/internal/tunnel-url \
          -d "{\"token\":\"$TOKEN\",\"url\":\"$url\"}"
      fi
    done
```

For production, named tunnels with a stable `tunnel.concerto.run/token` subdomain are the right solution. Quick tunnels are fine for v1.

### Failure mode 3: cloud-init ordering and apt locks

On Ubuntu 24.04, cloud-init `runcmd` runs after `unattended-upgrades` has already acquired the apt lock. This caused flaky provisioning — about 1 in 5 Droplets would hang on `apt-get install`.

The fix is to wait for the lock to release before running any apt commands:

```yaml
runcmd:
  - while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 2; done
  - apt-get update -qq
  # ... rest of install
```

Simple, but it took three failed provisions at 3am to figure out.

### The MCP connector

Once the user completes Claude OAuth in the browser terminal, the backend generates an MCP connector snippet:

```json
{
  "mcpServers": {
    "concerto": {
      "command": "npx",
      "args": ["-y", "@concerto/mcp-client"],
      "env": {
        "CONCERTO_TOKEN": "tok_xxxx",
        "CONCERTO_API": "https://api.concerto.run"
      }
    }
  }
}
```

The user pastes this into claude.ai's MCP settings. The MCP client connects back to the Concerto API, which proxies tool calls to the Claude Code instance running on the Droplet.

### What's next

The v1 limitation is one Droplet per account. The obvious next step is multi-agent support — provision multiple Droplets, route tool calls to the right one based on task context. The MCP layer makes this straightforward to add without changing the client-facing interface.

The cloud-init template, the ttyd systemd unit, and the WebSocket proxy are the parts I'd share first if you're building something similar. Happy to answer questions in the comments.

---

*concerto.run — Hosted ($39/mo) or BYOC ($99 one-time)*
