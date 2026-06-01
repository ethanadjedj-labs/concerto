# Concerto — orchestrate parallel Claude Code sessions over MCP

[![MCP Server](https://img.shields.io/badge/MCP-server-1f6feb)](https://modelcontextprotocol.io)
[![Website](https://img.shields.io/badge/concerto.run-live-0a7f3f)](https://concerto.run)

**Talk to Claude. Claude runs Claude Code, in parallel, on a managed VPS.**

Concerto is a hosted MCP server that lets a single Claude conversation (Desktop, Code,
or any MCP client) spawn, list, inspect, and kill multiple long-running Claude Code
sessions on a managed Linux machine. You stop juggling terminals; Claude does that
for you.

---

## Why this exists

Claude Code is fantastic at single, focused tasks. The moment you need **three of
them at once** — one refactor, one bug hunt, one feature spike — you're back to
managing tmux panes, copying logs into chat, and re-priming context every time you
switch. Concerto turns that orchestration into MCP tool calls that Claude itself
makes.

| Without Concerto | With Concerto |
|---|---|
| One terminal, one Claude Code at a time | N sessions running in parallel, one chat |
| Re-prime context every restart | Sessions persist between chats and devices |
| `tail -f` your own logs | Claude reads progress and reports back |
| Lose state when your laptop sleeps | Compute lives on a managed VPS |

---

## What it gives Claude (the 5 MCP tools)

Once Concerto is connected, your Claude conversation gets these tools — implemented
in [`installer/mcp_server.py`](installer/mcp_server.py):

| Tool | What it does |
|---|---|
| `concerto_build` | High-level "build/ship/run this" intent: plans, picks a workspace, spawns sessions to execute. |
| `start_claude_session` | Launch a fresh Claude Code agent with a prompt and a model. Returns a `session_id`. |
| `list_claude_sessions` | What's running, what finished, what failed — across all your sessions. |
| `get_claude_session` | Tail a session's output, check progress, see if it's done. |
| `kill_claude_session` | Stop a runaway session cleanly. |

Each session is a real Claude Code process on a real machine with a real filesystem,
real network, persistent git, and no chat-context ceiling on tool output.

---

## Quick install

Concerto is a **remote MCP server** — there is nothing to `pip install`. You sign up,
get a per-customer streamable-HTTP URL, and paste it into your MCP client.

### 1. Sign up

Pick a plan at **[concerto.run](https://concerto.run)**:

| Plan | Price | What you get |
|---|---|---|
| **Solo** | **$49 / month** | One managed VPS, parallel sessions, 5-minute setup. |
| **Pro** | **$99 / month** | Bigger VPS, more concurrent sessions, priority email support. |

Works with Claude Pro. Built for Claude Max (Max recommended for heavy parallel usage).

### 2. Get your MCP URL

Your dashboard at `concerto.run/dashboard` shows the connection URL — it looks like:

```
https://api.concerto.run/mcp-proxy/<your-buyer-token>/mcp
```

That token routes to *your* managed VPS. Keep it secret.

### 3. Wire it into your MCP client

**Claude Code CLI**

```bash
claude mcp add --transport http concerto https://api.concerto.run/mcp-proxy/<your-token>/mcp
```

**Claude Desktop / other JSON-config clients** — drop into your MCP config:

```json
{
  "mcpServers": {
    "concerto": {
      "type": "http",
      "url": "https://api.concerto.run/mcp-proxy/<your-token>/mcp"
    }
  }
}
```

That's it. Open a new conversation, ask Claude to "start two parallel sessions to
refactor X and audit Y," and watch.

---

## A 30-second example

```
You: Spin up two sessions — one to add Postgres indexes for our slow user-search
     query, and one to dig into why our build is failing on Node 22. Report back
     when each is done.

Claude: [calls start_claude_session × 2 → returns sess_A, sess_B]
        Both running. I'll check on them.

… 4 minutes later …

Claude: [calls list_claude_sessions, then get_claude_session on each]
        sess_A finished — added two btree indexes, query dropped from 1.8s → 40ms,
        PR opened.
        sess_B is still running, halfway through bisecting node_modules; I'll
        check again in a few.
```

You never touched a terminal.

---

## How it's built

- **Transport:** streamable-HTTP MCP, per-customer URL routed by an API gateway.
- **Auth:** OAuth 2.1 + PKCE with bearer-token fallback. See [`installer/mcp_server.py`](installer/mcp_server.py).
- **Compute:** a dedicated managed VPS per customer (provisioned on first signup),
  Claude Code installed, sessions live under `tmux`, output streamed back through
  MCP tool returns.
- **Server metadata:** canonical MCP server descriptor in [`server.json`](server.json),
  conforming to the [Official MCP Registry schema](https://modelcontextprotocol.io/registry).

Deep dive: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Find Concerto across the MCP ecosystem

We publish to every MCP discovery surface. Live and pending listings are tracked
in [`docs/DISTRIBUTION.md`](docs/DISTRIBUTION.md):

- **Official MCP Registry** (`registry.modelcontextprotocol.io`) — canonical entry,
  re-published on every release via [`.github/workflows/mcp-publish.yml`](.github/workflows/mcp-publish.yml).
- **GitHub MCP Registry**, **PulseMCP** — auto-ingested from the Official Registry.
- **Smithery**, **Glama**, **mcp.so**, **awesome-mcp-servers** — see DISTRIBUTION.md
  for direct links once each goes live.

---

## Repo map

| Path | What lives there |
|---|---|
| [`installer/`](installer/) | Cloud-init template + the standalone FastMCP server that runs on each customer VPS. |
| [`backend/concerto/`](backend/concerto/) | Control plane: signup, provisioning, MCP proxy router, OAuth, billing webhooks. |
| [`frontend/`](frontend/) | Marketing/landing site (Next.js) — also deployed from [concerto-frontend](https://concerto.run). |
| [`docs/`](docs/) | Architecture, runbook, security model, distribution status, launch kits. |
| [`server.json`](server.json) | Canonical MCP server metadata (Official Registry schema). |
| [`emails/`](emails/) | Transactional email templates. |
| [`skill-package/`](skill-package/) | Packaged Claude Skill for Concerto. |
| [`deploy/`](deploy/) | Infra deploy scripts. |

---

## Status

- **Production:** [concerto.run](https://concerto.run) is live and selling. See
  [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md) for the readiness
  matrix and [`docs/SECURITY.md`](docs/SECURITY.md) for the security model.
- **Version:** see [`server.json`](server.json) — current and previous releases
  publish to the Official MCP Registry automatically.

---

## Links

- Product & signup → **[concerto.run](https://concerto.run)**
- Docs index → [`docs/`](docs/)
- FAQ → [`docs/FAQ.md`](docs/FAQ.md)
- Distribution status → [`docs/DISTRIBUTION.md`](docs/DISTRIBUTION.md)
- License → [LICENSE](LICENSE)

---

*Concerto is a product of ethanadjedj-labs. Built with Claude Code, by people who
got tired of running Claude Code in one terminal at a time.*
