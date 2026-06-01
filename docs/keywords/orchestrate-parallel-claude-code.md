# How to orchestrate parallel Claude Code sessions

If you're trying to **run multiple Claude Code sessions in parallel** from a single
Claude conversation — refactoring one repo while bisecting a bug in another, or
fanning out a feature across three branches — there isn't an out-of-the-box answer.
Claude Code is single-process by default, and the moment you spin up a second one
you're back to tmux panes, terminal copy-paste, and re-priming context every time
you flip windows.

Concerto exists for this case.

## What "orchestration" actually requires

To run parallel Claude Code sessions cleanly you need:

1. **A persistent host.** Sessions need to outlive your laptop sleep/wake cycle.
   `nohup` and `screen` work, but managing them is its own job.
2. **A way for Claude to talk to those sessions.** Otherwise you're the orchestrator,
   not Claude.
3. **A way to read partial output without flooding chat.** Claude Code sessions can
   emit a lot. You need a tail/sample, not a firehose.
4. **A way to kill, restart, and resume cleanly.**

Concerto bundles all four behind five MCP tools — `start_claude_session`,
`list_claude_sessions`, `get_claude_session`, `kill_claude_session`, and the
high-level `concerto_build`. See [the main README](../../README.md#what-it-gives-claude-the-5-mcp-tools).

## Why doing this yourself is harder than it sounds

- **MCP transport plumbing.** Streamable-HTTP, OAuth 2.1 + PKCE, per-customer auth.
  Roughly 1,000 lines in [`installer/mcp_server.py`](../../installer/mcp_server.py).
- **Session lifecycle.** Spawning under `tmux`, tracking exit codes, tailing the
  scrollback to a bounded buffer.
- **Output truncation.** Tool returns can't be 50,000 lines; they need to be
  intelligently truncated with markers so Claude can ask for more if needed.
- **VPS provisioning.** If you want this on a real machine instead of your laptop,
  you need cloud-init, a tunnel, a firewall, and a way to update Claude Code.

## The shortcut

[Sign up at concerto.run](https://concerto.run), paste your MCP URL into your client,
and the orchestration is already wired up. Solo $49/month, Pro $99/month.

## Related

- [Run multiple Claude Code sessions →](./run-multiple-claude-code-sessions.md)
- [MCP orchestration explained →](./mcp-orchestration.md)
- [Architecture](../ARCHITECTURE.md)
