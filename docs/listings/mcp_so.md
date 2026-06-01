# mcp.so listing — Concerto

## Submission
Open a new issue at https://github.com/chatmcp/mcp-directory/issues/new.

### Title
Add Concerto — orchestrate parallel Claude Code sessions over MCP

### Body
```
**Name:** Concerto
**URL:** https://concerto.run
**Repo:** https://github.com/ethanadjedj-labs/concerto
**Category:** Developer Tools / Coding Agents
**Transport:** streamable-http (remote, OAuth 2.1)

**Description**
Concerto is an MCP server that turns Claude Code into a persistent, parallel,
remote work runtime. Each customer gets a managed VPS that runs long-lived
Claude Code sessions; the MCP endpoint exposes `start_claude_session`,
`list_claude_sessions`, `get_claude_session`, and `kill_claude_session`,
so any MCP-aware editor (Claude Desktop, Cursor, Zed, VS Code) can spawn
and inspect agents that survive between turns.

**Pricing:** Solo $49/mo, Pro $99/mo, BYOC supported.

**MCP URL pattern:** https://api.concerto.run/mcp-proxy/{buyer_token}/mcp

**Tools**
- concerto_build — natural-language plan to spawned Claude Code agent
- start_claude_session — new long-lived session
- list_claude_sessions — fleet view
- get_claude_session — transcript + state
- kill_claude_session — terminate

**Authoritative server.json:** https://github.com/ethanadjedj-labs/concerto/blob/main/server.json
```
