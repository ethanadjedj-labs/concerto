# Smithery listing — Concerto

Paste these fields into the Smithery submission form at https://smithery.ai/new.

## Server URL (URL-hosted submission)
```
https://api.concerto.run/mcp-proxy/{buyer_token}/mcp
```

## Display name
Concerto

## Tagline (80 chars)
Orchestrate parallel Claude Code sessions over MCP.

## Description (300 chars)
Concerto runs your Claude Code agents as long-lived sessions on a managed VPS and exposes them over MCP. Spawn, list, attach, inspect, and kill agents from your editor — context survives between turns, parallel work runs without you babysitting terminals.

## Categories
- Developer Tools
- Coding Agents
- AI Orchestration

## Authentication
- OAuth 2.1 + PKCE (preferred)
- Bearer token (legacy)

## Required runtime variable
- `buyer_token` (secret) — issued at signup on https://concerto.run

## Pricing
- Free trial
- Solo: $49/mo
- Pro: $99/mo

## Repository
https://github.com/ethanadjedj-labs/concerto

## Tools exposed
- `concerto_build(request)` — natural-language plan → spec → spawned Claude Code agent
- `start_claude_session(workdir, prompt, model)` — spin up a new Claude Code session
- `list_claude_sessions()` — every live session and its state
- `get_claude_session(session_id)` — full transcript + status
- `kill_claude_session(session_id)` — terminate a running session
