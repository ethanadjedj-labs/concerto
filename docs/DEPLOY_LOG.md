# Concerto Runtime Deploy Log

---

## 2026-06-01 — frontend restart picks up /learn/* SEO pages

**Service:** `concerto-frontend.service` (systemd, `next start -p 3500`)
**Build:** `.next/BUILD_ID = WkQ8PyKudBI2F0unPbo4A` (built 2026-06-01 18:50 UTC)
**Trigger:** `systemctl restart concerto-frontend`

### Why this was needed

Three SEO intent-keyword pages had been added to the source tree and a fresh
`npm run build` had completed, but the long-lived frontend process (started
2026-05-20) was still serving the stale bundle (`page-131c5843...js`). All
three `/learn/*` URLs returned HTTP 404 in production even though the static
HTML existed at `/opt/concerto-frontend/.next/server/app/learn/`.

### Verification (HTTP 200 from outside the box)

| URL | Status |
|-----|--------|
| `https://concerto.run/` | 200 |
| `https://concerto.run/learn/orchestrate-parallel-claude-code` | 200 |
| `https://concerto.run/learn/mcp-orchestration` | 200 |
| `https://concerto.run/learn/run-multiple-claude-code-sessions` | 200 |
| `https://concerto.run/sitemap.xml` | 200 (all 3 new URLs present, priority 0.8) |

### Risk

Zero new code, just picking up an already-tested build. Service has
`Restart=always`, so transient startup hiccups self-heal.

---

## 2026-05-23 — nf-prod-20260523-133129

**Tag:** `ghcr.io/ethanadjedj/concerto-runtime:nf-prod-20260523-133129`  
**Mutable alias:** `ghcr.io/ethanadjedj/concerto-runtime:nf-prod`  
**Digest:** `sha256:6e6fe977d74fe48732edb4d6b5832d544e9d7204949c57c8f83293d0f10835cc`  
**Built at:** 2026-05-23T13:31:29Z  
**Built by:** orchestrator-claude (sess_20260523T133129Z) on behalf of Ethan  
**Base image:** `node:20-bookworm` (sha256:8f693eaa7e0a...)

### Changes shipped

| # | Change | Source file | Status |
|---|--------|-------------|--------|
| 1 | `concerto_resume_session` MCP tool — resumes a finished session with prior context | `installer/mcp_server.py` | Shipped |
| 2 | `total_cost_usd_notional` stripped from MCP responses | `installer/mcp_server.py` | Shipped |
| 3 | Planner state-aware (`concerto_build` reads MANAGER_STATE before planning) | `installer/mcp_server.py` | Shipped |
| 4 | Envelope linter on session terminal (`_validate_envelope`) | `installer/mcp_server.py` | Shipped |
| 5 | State diff persisted to `state_diffs.json` on MANAGER_STATE change | `installer/mcp_server.py` | Shipped |
| 6 | Project-implicit scoping (`_detect_active_project`) | `installer/mcp_server.py` | Shipped |
| 7 | `concerto_replan(previous_plan_id, feedback)` tool with parent_plan_id audit trail | `installer/mcp_server.py` | Shipped |

### Build verification

- All 36 continuity tests passed prior to build (`backend/tests/test_continuity.py`)
- Dockerfile syntax check layer: `mcp_server.py syntax OK`
- Smoke test: all 9 required functions confirmed in built image via AST inspection
- No new pip dependencies (stdlib only additions)
- No DB schema changes

### Customer rollout

- **Active customers:** 0 paying (Ethan only)
- **Deploy risk:** zero
- **Existing service `concerto-pqyhhckm`** on old image `198cd2023352` — requires manual NF restart to pick up new image
- **`CONCERTO_NF_IMAGE`** in `/etc/cortex/env` points to mutable `nf-prod` tag — new customer provisions will automatically use this image

### Rollback

Prior image: `ghcr.io/ethanadjedj/concerto-runtime:nf-prod-before-v3-183730` (5a9e0d505167)
