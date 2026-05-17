# Maestro Installer

Cloud-init template + MCP server for the customer's DigitalOcean Ubuntu 22.04 droplet.

## Files

| File | Description |
|---|---|
| `cloud_init.yaml.j2` | Jinja2 template — rendered by empire backend and injected as DO user-data |
| `mcp_server.py` | Standalone copy of the MCP server (kept in sync with the embedded version in the template) |
| `test/dry_run.sh` | Local dry-run: renders template with fake values and validates YAML + Python imports |

## Jinja2 Template Variables

The empire backend renders `cloud_init.yaml.j2` with four variables before injecting into the DO API:

| Variable | Description |
|---|---|
| `maestro_token` | Per-provisioning callback token; identifies this droplet to the backend |
| `maestro_callback_url` | Backend webhook URL; receives the tunnel/bearer details when provisioning completes |
| `ssh_authorized_key` | Backend-generated RSA/Ed25519 public key; backend keeps the private side for terminal proxy |
| `customer_email` | Customer email for audit logs |

## Boot Sequence

```
DO API provisions Ubuntu 22.04 droplet
  └─ cloud-init runs user-data on first boot
       ├─ write_files (before runcmd)
       │    ├─ /etc/maestro/env           ← callback URL + provisioning token
       │    ├─ /etc/maestro/version       ← "1.0.0"
       │    ├─ /opt/maestro/mcp_server.py ← FastMCP server (Bearer auth, 4 tools)
       │    ├─ /etc/nginx/conf.d/maestro.conf ← reverse proxy config
       │    ├─ /etc/systemd/system/maestro-mcp.service
       │    ├─ /etc/systemd/system/maestro-tunnel.service
       │    ├─ /etc/systemd/system/maestro-ttyd.service
       │    └─ /opt/maestro/provision_complete.sh
       └─ runcmd (sequential, as root)
            ├─ apt install: curl python3-venv tmux git ttyd nginx
            ├─ NodeSource: Node.js 20 + npm
            ├─ npm install -g @anthropic-ai/claude-code
            ├─ cloudflared latest .deb from GitHub releases
            ├─ python3 -m venv /opt/maestro/.venv
            │    └─ pip install mcp[cli]>=1.2 anyio fastapi uvicorn[standard]
            ├─ openssl rand -hex 32 → /etc/maestro/token (chmod 600)
            ├─ mkdir /var/lib/maestro/sessions
            ├─ nginx -t && systemctl enable nginx
            ├─ systemctl daemon-reload
            ├─ systemctl enable+start: nginx, maestro-mcp, maestro-ttyd, maestro-tunnel
            └─ /opt/maestro/provision_complete.sh
                 ├─ polls journalctl -u maestro-tunnel for *.trycloudflare.com URL (up to 120s)
                 └─ POST {token, mcp_url, bearer_token, ttyd_url} → maestro_callback_url
```

## Port Map

| Service | Bind | Exposed via |
|---|---|---|
| `maestro-mcp` (MCP server) | `127.0.0.1:9876` | nginx → cloudflared |
| `maestro-ttyd` (web terminal) | `127.0.0.1:7681` | nginx `/terminal/` → cloudflared |
| nginx (reverse proxy) | `0.0.0.0:8080` | cloudflared quick tunnel |
| cloudflared | → `http://127.0.0.1:8080` | `*.trycloudflare.com` |

**URL layout** (single tunnel):
- `https://<hash>.trycloudflare.com/mcp` → MCP server
- `https://<hash>.trycloudflare.com/terminal/` → ttyd web terminal (WebSocket)

## Callback Payload

When provisioning completes, `provision_complete.sh` POSTs to `maestro_callback_url`:

```json
{
  "token": "<maestro_token>",
  "mcp_url": "https://<hash>.trycloudflare.com",
  "bearer_token": "<hex32 from /etc/maestro/token>",
  "ttyd_url": "https://<hash>.trycloudflare.com/terminal"
}
```

The backend stores `mcp_url` and `bearer_token` and displays them to the customer as the MCP connector config.

## MCP Server Tools

The MCP server exposes 4 tools over streamable HTTP (mcp>=1.2):

| Tool | Description |
|---|---|
| `start_claude_session(prompt, model?)` | Runs `claude -p <prompt> --output-format stream-json` in background; returns `session_id` immediately |
| `list_claude_sessions()` | Lists all sessions with id, status, model, prompt preview |
| `get_claude_session(session_id)` | Returns full output (last 500 lines) + exit_code for a session |
| `kill_claude_session(session_id)` | Cancels running session via asyncio task cancellation (→ SIGTERM to claude) |

All requests require `Authorization: Bearer <token>` where the token is the contents of `/etc/maestro/token`.

## Keeping `mcp_server.py` in Sync

`installer/mcp_server.py` is the canonical source. The `write_files` block in `cloud_init.yaml.j2` contains an identical copy. When updating the MCP server, edit both files and run `test/dry_run.sh --check-sync` to verify they match.

## Rendering the Template (backend pseudocode)

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("installer/"))
template = env.get_template("cloud_init.yaml.j2")
user_data = template.render(
    maestro_token=provisioning_token,
    maestro_callback_url=callback_url,
    ssh_authorized_key=customer_pubkey,
    customer_email=customer_email,
)

# Inject into DO API
droplet = do_client.droplets.create(
    name=f"maestro-{customer_id}",
    region="nyc3",
    size="s-1vcpu-2gb",
    image="ubuntu-22-04-x64",
    user_data=user_data,
    ssh_keys=[],  # managed via write_files authorized_keys above
)
```
