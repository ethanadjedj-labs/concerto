# MCP orchestration — when one MCP server commands other agents

Most MCP servers are *adapters* — they connect Claude to a database, a search index,
a file system, an API. **Orchestration MCP servers** are different: they connect
Claude to other *Claude agents*. The tools they expose are verbs like *start*,
*list*, *get progress*, *kill* — the language of a process manager, not a query
layer.

Concerto is one of the first production MCP servers in this category, dedicated to
orchestrating Claude Code.

## Why this is its own category

A normal MCP adapter is stateless from the agent's perspective: tool call → data →
done. Orchestration servers carry **long-lived state** the agent has to manage:

| Concern | Adapter MCP | Orchestration MCP |
|---|---|---|
| Tool semantics | Read / write data | Start / monitor / kill agents |
| State | Stateless or DB-backed | Per-session lifecycle (running, exited, killed) |
| Latency | Sub-second | Minutes to hours per session |
| Output shape | Small JSON | Streaming, truncated, paginated logs |
| Failure mode | Tool returns error | Subprocess crashes, OOMs, hangs |

Concerto handles all four of those — see [`installer/mcp_server.py`](../../installer/mcp_server.py).

## The five orchestration verbs

Once you've decided to build an orchestration MCP server, the verbs converge.
Concerto exposes:

```
concerto_build(request)            # high-level: plan + spawn
start_claude_session(prompt, model) # explicit spawn
list_claude_sessions()              # what's running
get_claude_session(session_id)      # progress + tail
kill_claude_session(session_id)     # stop cleanly
```

That shape is general — any orchestration MCP server (Claude Code, Codex, OpenAI
agents, custom worker processes) will land on a near-identical surface.

## Why the conversation flows differently

With an adapter MCP, you write a prompt and Claude responds in chat. With an
orchestration MCP, *Claude itself becomes a coordinator*:

> *"Spin up two sessions — one to refactor the User model, one to update the
> migration. Check in every five minutes. Don't kill either unless I say so."*

That instruction Claude can actually execute. It calls `start_claude_session` twice,
then loops on `list_claude_sessions` + `get_claude_session`, reporting back. You're
out of the inner loop.

## Try it

Concerto is the simplest way to get hands-on with MCP orchestration without
building it yourself.

- **Solo:** $49 / month
- **Pro:** $99 / month

→ **[concerto.run](https://concerto.run)**

## Related

- [Orchestrate parallel Claude Code →](./orchestrate-parallel-claude-code.md)
- [Run multiple Claude Code sessions →](./run-multiple-claude-code-sessions.md)
- [Architecture deep-dive](../ARCHITECTURE.md)
- [Distribution across MCP registries](../DISTRIBUTION.md)
