# Concerto Real Product Audit — 2026-05-17T18:00:00Z

**Verdict: CONDITIONAL_ON** — not ready for first paying customer until blocker actions 1–5 in MANAGER_STATE are resolved by operator. The code itself now passes the static audit after this PR's fixes.

---

## Phase 1 — Static Audit Results

### Stripe checkout → buyer creation
| Check | Result |
|-------|--------|
| Webhook endpoint exists at `/webhooks/stripe-concerto` | ✅ |
| Signature verification logic correct | ✅ (after fix: env var was `STRIPE_WEBHOOK_SECRET_CONCERTO` but should be `STRIPE_CONCERTO_WEBHOOK_SECRET`) |
| Idempotency guard on duplicate events | ✅ |
| Buyer row insertion with plan, email, token | ✅ |
| Confirmation email sent via Resend | ✅ (conditional on `RESEND_API_KEY` + verified domain) |
| `STRIPE_CONCERTO_WEBHOOK_SECRET` not set in `/etc/cortex/env` | ❌ BLOCKER — webhook returns 401 on every purchase |

### Buyer status polling
| Check | Result |
|-------|--------|
| `/api/buyer/<token>/status` shape correct | ✅ |
| Returns `refund_eligible`, `refund_window_open` | ✅ |
| `/api/buyer/<token>/oauth-status` shape | ✅ |
| SSH check cached 30s | ✅ |

### Setup form validation
| Check | Result |
|-------|--------|
| BYOC: missing DO key → 422 | ✅ |
| Invalid DO key format → client-side error | ✅ |
| **Invalid DO key → provisioner gets 401 → status `api_key_invalid`** | ✅ |
| **Pre-flight DO key check before provisioning** | ✅ (added in this PR: `/api/preflight-do-key`) |
| Refunded buyer cannot re-provision | ✅ (fixed: `refunded` removed from allowed states) |

### Dashboard state machine
| Status | Frontend renders | Crash? |
|--------|-----------------|--------|
| `paid_unprovisioned` | Setup form | No |
| `provisioning` | Spinner step | No |
| `installing` | Installing step | No |
| `awaiting_oauth` | OAuth step with copy fields | No |
| `active` / `ready` | Ready state + MCP URL | No |
| `failed_install` | Error card with refund CTA | No |
| `api_key_invalid` | Bilingual error card | No |
| `account_no_credit` | Error card | No |
| `refunded` | Refunded banner | No |
| `suspended` | Suspended banner | No |

### Cloud-init rendering
| Check | Result |
|-------|--------|
| Template loads from correct path | ✅ |
| All required vars passed (token, ssh_authorized_key, ttyd_password, etc.) | ✅ (fixed: `concerto_token_prefix` was missing) |
| apt packages installed: curl, python3-venv, tmux, git, ttyd, nginx | ✅ |
| Claude Code installed via npm: `@anthropic-ai/claude-code` | ✅ |
| cloudflared installed from GitHub releases | ✅ |
| MCP server venv created | ✅ |
| Bearer token generated: `openssl rand -hex 32 > /etc/concerto/token` | ✅ |
| nginx reverse proxy: port 8080 → MCP (9876) + ttyd (7681/terminal) | ✅ |
| cloudflared tunnel tunnels port 8080 | ✅ |
| Completion callback: `provision_complete.sh` polls log and POSTs to empire | ✅ |
| Workspace seeded at `/opt/concerto-workspace/` | ✅ |

### MCP server
| Check | Result |
|-------|--------|
| 4 tools: start_claude_session, list_claude_sessions, get_claude_session, kill_claude_session | ✅ |
| Bearer auth middleware | ✅ |
| `/healthz` unauth'd | ✅ |
| Listens on 127.0.0.1:9876 (behind nginx on 8080) | ✅ |
| Uses anyio subprocess to spawn `claude -p` | ✅ |

---

## Phase 2 — Real Provisioning Test

**SKIPPED**: `CONCERTO_DO_API_TOKEN` not set in `/etc/cortex/env`. Phase 2 cannot proceed without it.
This is MANAGER_STATE blocker #4.

---

## Phase 3 — Failure Injection (Static Analysis)

| Failure Mode | Code Path | Result |
|-------------|-----------|--------|
| Invalid DO key (BYOC) | `DOAuthError` → status `api_key_invalid` | ✅ handled |
| DO 402 no credit | `DOCreditError` → status `account_no_credit` | ✅ handled |
| Droplet boot error | `DropletBootError` → auto-refund triggered | ✅ handled |
| Provisioning timeout | `TimeoutError` → auto-refund triggered | ✅ handled |
| Cloud-init timeout (8min) | `_cloud_init_timeout_watch` → status `failed_install` + auto-refund | ✅ handled |
| Cloudflared tunnel fails | `mcp_url == "tunnel_failed"` → operator alert + MANAGER_STATE entry | ✅ handled |
| **Refund: hosted droplet NOT destroyed** | `provider == "hosted"` check — **WRONG FIELD** | ❌ BUG — fixed in this PR |
| **Refund: DO API key wrong** | `DO_PROVISIONER_API_KEY` not set | ❌ BUG — fixed in this PR |
| **Monitoring: hosted buyers not checked** | `provider = 'hosted'` query — **WRONG FIELD** | ❌ BUG — fixed in this PR |

---

## Phase 4 — Runbook Drift Found and Fixed

| Issue | Lines | Fix Applied |
|-------|-------|-------------|
| `STRIPE_WEBHOOK_SECRET` → `STRIPE_CONCERTO_WEBHOOK_SECRET` | 29, 530 | ✅ |
| `ORDER BY created_at DESC` — column doesn't exist, should be `paid_at` | 90, 136, 184, 426, 735 | ✅ |
| `do_droplet_id` — column doesn't exist, should be `vps_id` | 234, 666, 681, 703, 735 | ✅ |
| `tunnel_url` — column doesn't exist, should be `mcp_url` | 292, 666, 735 | ✅ |
| `refunded_at=datetime('now')` — wrong format (stores TEXT, schema wants INTEGER) | 213, 377, 714 | ✅ → `strftime('%s','now')` |

---

## Phase 5 — Fixes Applied

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `backend/concerto/stripe_webhook.py` | Webhook secret env var `STRIPE_WEBHOOK_SECRET_CONCERTO` → `STRIPE_CONCERTO_WEBHOOK_SECRET` | Fixed |
| 2 | `backend/concerto/refunds.py` | `provider == "hosted"` check uses wrong field | Fixed → `plan == "hosted"` |
| 3 | `backend/concerto/refunds.py` | `DO_PROVISIONER_API_KEY` env var wrong | Fixed → `CONCERTO_DO_API_TOKEN` |
| 4 | `backend/concerto/monitoring.py` | `provider = 'hosted'` SQL query wrong | Fixed → `plan = 'hosted'` |
| 5 | `backend/concerto/server.py` | CORS blocks Cloudflare preview URL | Fixed → `CONCERTO_EXTRA_ORIGINS` env var |
| 6 | `backend/concerto/provisioner.py` | `concerto_token_prefix` missing from Jinja2 render | Fixed |
| 7 | `backend/concerto/customer_portal.py` | `stripe.error.StripeError` → deprecated | Fixed → `stripe.StripeError` |
| 8 | `backend/concerto/provision_router.py` | `refunded` allowed to re-provision | Fixed: removed from allowed states |
| 9 | `backend/concerto/preflight_router.py` | Missing `/api/preflight-do-key` endpoint | Added |
| 10 | `backend/concerto/server.py` | preflight router not wired | Fixed |
| 11 | `frontend/app/setup/[token]/page.tsx` | No preflight check before provisioning | Fixed |
| 12 | `docs/RUNBOOK.md` | 5 categories of column/env name drift | Fixed |
| 13 | `ops/scripts/recover_stuck_droplet.sh` | Missing recovery script | Added |
| 14 | `ops/scripts/force_refund_buyer.sh` | Missing recovery script | Added |
| 15 | `ops/scripts/rescue_failed_oauth.sh` | Missing recovery script | Added |

---

## Phase 6 — Pre-flight DO Key Check

**Added**: `backend/concerto/preflight_router.py` — `POST /api/preflight-do-key`

- Validates key format (`dop_v1_` prefix)
- Makes real `GET /v2/account` call to DigitalOcean
- Returns `{ok: true, account_email, droplet_limit}` on success
- Returns structured errors for: empty key, invalid format, 401, 403, timeout, network error
- **Frontend integrated**: `setup/[token]/page.tsx` calls preflight before `POST /api/provision` for BYOC plan

---

## Phase 7 — Cost Incurred

**$0.00** — Phase 2 skipped (no DO token). No infrastructure created.

---

## Remaining Operator Actions (ranked by criticality)

| # | Action | Criticality |
|---|--------|-------------|
| 1 | Register Stripe webhook + set `STRIPE_CONCERTO_WEBHOOK_SECRET` in `/etc/cortex/env` | 🔴 LAUNCH BLOCKER — without this, zero sales work |
| 2 | Set `CONCERTO_DO_API_TOKEN` in `/etc/cortex/env` | 🔴 LAUNCH BLOCKER — hosted plan cannot provision |
| 3 | NameSilo NS → Cloudflare (jonah + kiki) | 🔴 LAUNCH BLOCKER — DNS doesn't resolve |
| 4 | Vercel: import concerto, add domain, set env vars | 🔴 LAUNCH BLOCKER — frontend unreachable |
| 5 | Resend: add + verify `concerto.run` domain | 🔴 LAUNCH BLOCKER — emails don't send |
| 6 | Set `CONCERTO_EXTRA_ORIGINS` if using preview URL for testing | 🟡 Dev/test only |
| 7 | Start timers: `systemctl start concerto-hosted-lifecycle.timer concerto-drip-runner.timer concerto-status-writer.timer concerto-monitoring.timer` | 🟡 Within 48h post-launch |
| 8 | `mkdir -p /var/www/concerto-status && chown www-data:www-data /var/www/concerto-status` | 🟡 Status page prereq |
| 9 | Set `DISCORD_INVITE_URL` in `/etc/cortex/env` | 🟡 Support infra |
| 10 | Run `npm run build` from `/opt/concerto/frontend` and verify 0 TS errors | 🟡 Before deploy |

---

## Recovery Script Inventory

| Script | Purpose |
|--------|---------|
| `ops/scripts/recover_stuck_droplet.sh <token>` | Reset stuck provisioning/installing buyer to retriable state |
| `ops/scripts/force_refund_buyer.sh <token> [--destroy-droplet]` | Mark buyer refunded in DB + optionally destroy DO droplet |
| `ops/scripts/rescue_failed_oauth.sh <token>` | SSH-diagnose + re-send setup email for stuck OAuth buyers |
