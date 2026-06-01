# Glama listing — Concerto

**Why this listing is now load-bearing:** PR #7242 on `punkpeye/awesome-mcp-servers` is gated on a Glama listing + score badge by the `glama-check` GitHub Action. Until this listing exists, that PR cannot merge. See [`awesome_mcp_pr_response.md`](awesome_mcp_pr_response.md) for the post-listing PR-update recipe.

## Submission — two surfaces, do both

Concerto is a **hosted remote MCP server** (streamable-HTTP, OAuth 2.1), so the
right primary surface is `glama.ai/mcp/connectors` rather than the
container-bundle directory. The bot comment on PR #7242 confirms this:

> P.S. If your server already has a hosted endpoint, you can also list it under https://glama.ai/mcp/connectors.

### A. Servers directory (`glama.ai/mcp/servers`) — for the badge

1. Open https://glama.ai/mcp/servers
2. Click **Add Server**
3. Paste GitHub URL: `https://github.com/ethanadjedj-labs/concerto`
4. Glama indexes the README, `server.json`, and release tags.
5. Once indexed, the score badge is live at
   `https://glama.ai/mcp/servers/ethanadjedj-labs/concerto/badges/score.svg`
   — needed for PR #7242.

### B. Connectors directory (`glama.ai/mcp/connectors`) — for the hosted endpoint

1. Open https://glama.ai/mcp/connectors
2. Click **Add Connector**
3. URL template: `https://api.concerto.run/mcp-proxy/{buyer_token}/mcp`
4. Auth: OAuth 2.1 (Concerto issues per-buyer tokens at signup)
5. Transport: `streamable-http`

## Glama validation prerequisites — current status

| Check | Status | Where |
|---|---|---|
| Public GitHub repo | ✅ | https://github.com/ethanadjedj-labs/concerto |
| README with install snippet | ✅ | Root `README.md` (updated for distribution) |
| Working examples / quickstart | ✅ | `docs/QUICKSTART.md` + `installer/README.md` |
| Released version tag | ⚠️ READY-FOR-ETHAN | Tag `v1.0.0` after first publish; CI does this on release |
| Docker buildability | N/A | Concerto is a hosted remote MCP server, not a containerised stdio bundle |
| `server.json` at root | ✅ | `/server.json` per Official MCP Registry schema |

## Description (paste into the long-form field once submitted)

Concerto is the orchestration layer for Claude Code. Each customer gets a managed VPS (or BYOC) running long-lived Claude Code sessions exposed over MCP — your editor talks to `https://api.concerto.run/mcp-proxy/<your-token>/mcp` and the same tools (`start_claude_session`, `list_claude_sessions`, `get_claude_session`, `kill_claude_session`) work across every MCP-aware client (Claude Desktop, Cursor, Zed, VS Code, your own).

Why people use it:
- **Parallel Claude Code sessions** without juggling terminals or losing context.
- **State persists between turns.** Each session is a long-running tmux + ttyd process — kill your laptop, the work continues.
- **One MCP endpoint, every client.** Streamable-HTTP transport with OAuth 2.1.
- **Real audit trail.** Every keystroke + tool call is logged per buyer.

Pricing: Solo $49/mo, Pro $99/mo. BYOC available.
