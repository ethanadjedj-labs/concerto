# Concerto Architecture

## System Diagram

```
                         ┌─────────────────────────────────────────────┐
                         │              Customer Browser                │
                         └───────────────────┬─────────────────────────┘
                                             │ HTTPS
                                             ▼
                         ┌─────────────────────────────────────────────┐
                         │           concerto.run  (Next.js)            │
                         │   landing · checkout · dashboard · setup     │
                         └──────────┬──────────────────────┬───────────┘
                                    │ Stripe Checkout       │ REST /api
                                    ▼                       ▼
                    ┌───────────────────────┐  ┌───────────────────────────┐
                    │   Stripe              │  │  Concerto Backend          │
                    │   (payment, webhook)  │  │  FastAPI + SQLite         │
                    └───────────┬───────────┘  │  (DO provisioning,        │
                                │ webhook       │   session mgmt, JWT)      │
                                └──────────────┤                           │
                                               └───────────┬───────────────┘
                                                           │ DO API v2
                                                           ▼
                                               ┌───────────────────────────┐
                                               │  DigitalOcean API         │
                                               │  (Droplet create/destroy) │
                                               └───────────┬───────────────┘
                                                           │ cloud-init
                                                           ▼
                         ┌─────────────────────────────────────────────────┐
                         │           Customer Droplet  (DO)                │
                         │   Ubuntu 24.04, 2 vCPU, 4 GB RAM               │
                         │                                                 │
                         │   ┌─────────────┐   ┌─────────────────────┐   │
                         │   │ Claude Code  │   │ MCP Server (stdio)  │   │
                         │   │ (node + npm) │◄──│ (concerto-mcp-relay) │   │
                         │   └─────────────┘   └──────────┬──────────┘   │
                         │                                 │               │
                         │   ┌─────────────┐              │               │
                         │   │ ttyd         │◄─────────────┘              │
                         │   │ (web term)   │                              │
                         │   └──────┬──────┘                              │
                         └──────────┼──────────────────────────────────────┘
                                    │ cloudflared tunnel (outbound only)
                                    ▼
                         ┌─────────────────────────────────────────────┐
                         │          Cloudflare Tunnel                  │
                         │  (unique per droplet, no inbound ports)     │
                         └───────────────────────┬─────────────────────┘
                                                 │ wss
                                                 ▼
                         ┌─────────────────────────────────────────────┐
                         │              claude.ai                      │
                         │    MCP Connector → live Claude Code tools   │
                         └─────────────────────────────────────────────┘
```

## Components

| Component | Tech | Responsibility |
|-----------|------|----------------|
| `concerto.run` frontend | Next.js / Vercel | Landing page, Stripe checkout, setup wizard, dashboard |
| Concerto backend | FastAPI + SQLite | Stripe webhook handling, DO API calls, JWT issuance, session state |
| DigitalOcean API | DO v2 REST | Droplet CRUD (create, power-off, destroy) |
| `cloud-init` installer | Bash (`install.concerto.run`) | Installs Claude Code, MCP server, ttyd, cloudflared; hardens firewall |
| Claude Code | Node.js / npm | Agentic coding assistant running on the droplet |
| `concerto-mcp-relay` | Python (stdio) | Bridges MCP protocol over the cloudflared tunnel |
| ttyd | Binary | Web-based terminal for one-time Claude OAuth; tunnel-only, not internet-exposed |
| cloudflared | Binary | Persistent outbound tunnel; the only network path into the droplet |
| Stripe | SaaS | Payment processing, webhook delivery |
| claude.ai | SaaS | Customer-facing Claude interface; reads MCP connector config |

## Latency Budget

| Segment | Typical | Notes |
|---------|---------|-------|
| Stripe checkout → backend webhook | < 5 s | Stripe retries for 72 h |
| Backend webhook → DO API create | < 1 s | REST call |
| DO API create → Droplet ACTIVE | 20–40 s | DO SLA |
| cloud-init install (all deps) | 90–180 s | Depends on package mirror speed |
| cloudflared tunnel ready | < 5 s after cloud-init | Auto-starts via systemd |
| MCP tool call round-trip | 50–200 ms | Tunnel + localhost MCP relay |
| Claude OAuth (user-driven) | 30–60 s | One-time, interactive |

**Total provisioning (Stripe → ready):** ~3–5 minutes under normal conditions.

## Security Boundaries

```
[ Internet ]
     │
     │  No direct inbound ports (ufw default deny)
     │
     ▼
[ cloudflared ]  ← outbound-only; Cloudflare auth required
     │
     ▼
[ MCP relay / ttyd ]  ← localhost only; not accessible without tunnel
     │
     ▼
[ Claude Code ]  ← runs as non-root user; isolated to /home/concerto
```

- The droplet has **no open inbound ports** (ufw denies all; cloudflared is outbound).
- ttyd is bound to `127.0.0.1` only; reachable solely through the Cloudflare tunnel.
- The customer's DO API key is used once during provisioning and stored encrypted-at-rest in the backend SQLite database. It is never transmitted to the droplet.
- SSH is disabled in the cloud-init default configuration (optional: customer can add their own key — see [SECURITY.md](SECURITY.md)).

## Data Flows

| Data | Path | Storage |
|------|------|---------|
| DO API key | Browser → backend (TLS) | Backend SQLite, AES-256 encrypted |
| Customer email | Stripe webhook → backend | Backend SQLite |
| Cloudflare tunnel token | Backend → droplet (cloud-init user data) | Ephemeral; not logged |
| Claude conversations | claude.ai → cloudflared → MCP relay → Claude Code | Never stored by Concerto |
| Droplet files/code | Stays on the customer's DO Droplet | Customer-owned |

## Deployment Topology

```
Concerto backend: single Hetzner VPS (or DO Droplet) — FastAPI + SQLite
Frontend:        Vercel (Next.js, edge CDN)
Customer droplets: DigitalOcean (customer's own account, customer-billed)
Tunnel:          Cloudflare (free tier per droplet)
Email:           Resend transactional
```
