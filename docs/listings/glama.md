# Glama listing — Concerto

## Submission
1. Open https://glama.ai/mcp/servers
2. Click **Add Server**
3. Paste: `https://github.com/ethanadjedj-labs/concerto`
4. Submit. Glama indexes the README, schemas, and release tags automatically.

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
