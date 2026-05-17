# Maestro

**Remote workshop for Claude Code agents.**

Customer pays $99 → enters DigitalOcean API key → backend provisions VPS in their DO account with Claude Code + MCP server + cloudflared preinstalled → customer OAuths Claude via embedded web terminal (~30s) → pastes connector config in claude.ai → live.

From any claude.ai conversation, the customer pilots agentic Claude Code on their dedicated VPS.

## Architecture

```
Customer pays $99 (Stripe)
  → enters DigitalOcean API key
  → backend provisions VPS (DO Droplet, Claude Code + MCP + cloudflared)
  → embedded web terminal for Claude OAuth
  → connector config displayed
  → paste into claude.ai → live in ~30s
```

## Repo structure

- `frontend/` — Next.js customer portal (payment, onboarding, dashboard)
- `backend/` — FastAPI provisioning service (Stripe webhooks, DO API, session mgmt)
- `installer/` — Bash installer script delivered via install.maestro.run
- `docs/` — Product docs, architecture diagrams, email copy

## Development

Documentation and implementation in progress. See branch `feat/frontend-v1`, `feat/backend-v1`, `feat/installer-v1`, `feat/docs-and-emails-v1`.
