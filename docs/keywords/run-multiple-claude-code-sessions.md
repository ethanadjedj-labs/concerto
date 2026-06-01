# Run multiple Claude Code sessions at once

The honest answer to *"can I run multiple Claude Code sessions in parallel?"* is
**yes — but Claude Code itself won't orchestrate them.** It runs one process at a
time. You can open three terminals and start three independent sessions, but then
*you* are the orchestrator: switching tabs, copying output around, remembering which
session is which.

This page covers the three real options.

## Option 1: do it manually (free, painful)

```bash
# Terminal 1
cd ~/code/api && claude --model claude-sonnet-4-6
# Terminal 2
cd ~/code/web && claude --model claude-sonnet-4-6
# Terminal 3
cd ~/code/infra && claude --model claude-opus-4-7
```

Works fine for two sessions. Falls apart at three because *you* are now the
human MCP between them.

## Option 2: write your own MCP wrapper

If you want Claude to orchestrate, you need an MCP server that exposes
`start/list/get/kill` for Claude Code processes. The basic shape is:

```python
@mcp.tool()
async def start_claude_session(prompt: str, model: str) -> dict:
    session_id = uuid()
    subprocess.Popen([
        "tmux", "new-session", "-d", "-s", f"claude-{session_id}",
        "claude", "--print", prompt, "--model", model,
    ])
    return {"session_id": session_id}
```

…plus output capture, lifecycle tracking, auth, transport. The real implementation
in [`installer/mcp_server.py`](../../installer/mcp_server.py) is ~1,000 lines for
good reason: streaming HTTP, OAuth 2.1 + PKCE, scrollback buffering, dead-session
cleanup, multi-tenant routing.

## Option 3: use Concerto

A hosted MCP server that does all of the above and runs sessions on a managed VPS
so they survive your laptop closing. Five tools, one connection string.

- **Solo:** $49 / month — one managed VPS, parallel sessions, persistent.
- **Pro:** $99 / month — bigger VPS, more concurrent sessions, priority support.

[Sign up at concerto.run](https://concerto.run).

## What "parallel" actually buys you

In practice, the moment you can run three sessions concurrently you start using
Claude Code differently:

- **Fan-out exploration.** Three sessions investigating three suspect commits for a
  regression, in parallel, instead of bisecting sequentially.
- **Long-running background work.** Spin a session to migrate a schema while
  another opens a PR for a feature flag in the same repo.
- **Free chat from blocking.** Your chat with Claude isn't held hostage by a
  10-minute `npm install` — that's running over there, on the VPS.

## Related

- [Orchestrate parallel Claude Code →](./orchestrate-parallel-claude-code.md)
- [MCP orchestration →](./mcp-orchestration.md)
- [FAQ](../FAQ.md)
