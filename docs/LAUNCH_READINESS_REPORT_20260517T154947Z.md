# Concerto Launch Readiness Report
**Generated**: 2026-05-17T15:49:47Z  
**Auditor**: Claude Sonnet 4.6 (automated)  
**Branch**: chore/launch-readiness-audit-v1  
**Repo**: https://github.com/ethanadjedj-labs/concerto  
**Prerequisite PRs merged**: #22 (rebrand), #23 (SEO/OG), #24 (operator runbook)

---

## VERDICT

```
READY_TO_LAUNCH: CONDITIONAL_ON: [
  NS propagation at NameSilo,
  Vercel deployment + custom domain,
  Stripe webhook registered + STRIPE_CONCERTO_WEBHOOK_SECRET set,
  Resend concerto.run domain verified,
  CONCERTO_DO_API_TOKEN set in /etc/cortex/env
]
```

**Blockers**: 5  
**Recommended**: 7  
**Auto-fixes applied**: 2

---

## A. Code Quality

| Check | Status | Detail |
|-------|--------|--------|
| `npm run build` | ✅ PASS | 20 routes compiled, 0 errors |
| `python -m py_compile` | ✅ PASS | All `backend/concerto/**/*.py` compile clean |
| TypeScript strict (`tsc --noEmit`) | ✅ PASS | 0 errors |
| ESLint | ✅ FIXED | No config existed → created `frontend/.eslintrc.json` (next/core-web-vitals); `npm run lint` now passes with 0 warnings |
| `cloud_init.yaml.j2` Jinja2 parse | ✅ PASS | Parsed without error |

**Build routes** (20 total):  
`/`, `/dashboard/[token]`, `/dashboard/[token]/subscription`, `/help`, `/hero-demo`,  
`/legal/{aup,privacy,refund,terms}`, `/opengraph-image`, `/setup/[token]`, `/sitemap.xml`,  
`/status`, `/success`, `/api/checkout`, `/api/status`, `/apple-icon`, `/icon`, `/twitter-image`

---

## B. Repo Hygiene

| Check | Status | Detail |
|-------|--------|--------|
| README.md present, Concerto references | ✅ PASS | 8 references, install instructions present |
| LICENSE | ✅ PASS | MIT License (2026 Ethan Adjedj) |
| `.gitignore` coverage | ✅ FIXED | Missing `*.db`, `*.db.backup` — added |
| Secrets scan | ✅ PASS | No hardcoded keys/tokens (only `process.env.X` / `os.getenv()` references) |
| Leftover "maestro" strings | ✅ PASS | 2 intentional in RUNBOOK.md (brand-check checklist item + historical MANAGER_STATE ref), 1 in server.py (migration filename `008_rename_maestro_to_concerto.sql`) |

---

## C. Live Deployment (preview: `jet-graduates-pursuant-victoria.trycloudflare.com`)

> **Note**: Running Next.js serves build from `/tmp/concerto-rename/maestro/frontend` (stale — from rebrand session). The new SEO/OG routes from PR #23 are in the repo but NOT in the running instance. Rebuild required (operator action).

| Route | Code | Status |
|-------|------|--------|
| `/` | 200 | ✅ PASS |
| `/robots.txt` | 404 | ⚠️ STALE BUILD — `public/robots.txt` exists in repo |
| `/sitemap.xml` | 404 | ⚠️ STALE BUILD — `app/sitemap.ts` exists in repo |
| `/favicon.ico` | 404 | ⚠️ STALE BUILD — `app/icon.tsx` dynamic route exists |
| `/opengraph-image` | 404 | ⚠️ STALE BUILD — `app/opengraph-image.tsx` exists |

**HTML meta tags on `/`** (from old build — layout.tsx has all):
- `og:title` ✅, `og:description` ✅, `og:url` ✅, `og:site_name` ✅, `og:type` ✅
- `twitter:card` ✅, `twitter:title` ✅, `twitter:description` ✅
- `og:image` ⚠️ not in old build HTML — configured as `/opengraph-image` in new layout.tsx
- JSON-LD: Organization + WebSite + 2× Product schemas ✅ (in layout.tsx, rendered in all pages)

**Legal pages** (code): `aup`, `privacy`, `refund`, `terms` all exist in `frontend/app/legal/` ✅

---

## D. Backend Services (empire VPS)

| Check | Status | Detail |
|-------|--------|--------|
| `concerto-backend.service` | ✅ active | `{"status":"ok","service":"concerto-backend"}` |
| `curl localhost:8090/healthz` | ✅ 200 | Response as above |
| DB tables | ✅ PASS | `concerto_buyers`, `concerto_hosted_pool`, `stripe_processed_events` |
| concerto-hosted-lifecycle.timer | ⚠️ enabled/inactive | Installed + enabled, never started. No trigger time. |
| concerto-drip-runner.timer | ⚠️ enabled/inactive | Same |
| concerto-status-writer.timer | ⚠️ enabled/inactive | Same |
| concerto-monitoring.timer | ⚠️ enabled/inactive | Same |
| `/var/www/concerto-status/status.json` | ❌ MISSING | Directory `/var/www/concerto-status/` does not exist |

**Fix for timers** (operator):
```bash
systemctl start concerto-hosted-lifecycle.timer concerto-drip-runner.timer \
  concerto-status-writer.timer concerto-monitoring.timer
mkdir -p /var/www/concerto-status && chown www-data:www-data /var/www/concerto-status
```

---

## E. Stripe Integration

| Check | Status | Detail |
|-------|--------|--------|
| Concerto product active | ✅ PASS | `prod_UXB4GjfiVkvuW9`: Concerto ($99 BYOC) — active |
| Concerto Hosted product active | ✅ PASS | `prod_UXB4UqlFW0OLbP`: Concerto Hosted ($39/mo) — active |
| Webhook for `api.concerto.run` | ❌ MISSING | Only `strandedgrid.com/stripe/webhook` registered. No `api.concerto.run/webhooks/stripe-concerto`. |
| `STRIPE_CONCERTO_WEBHOOK_SECRET` in env | ❌ MISSING | Not set in `/etc/cortex/env`. Webhook handler will reject all events. |
| Stripe Tax | ⚠️ PENDING | `status: "pending"`, `head_office: null`. Tax not collecting. |

---

## F. DNS + Cloudflare

| Check | Status | Detail |
|-------|--------|--------|
| `dig concerto.run NS @1.1.1.1` | ❌ NO RESULT | Zone status `pending` — NS not updated at NameSilo |
| Cloudflare zone status | ⚠️ PENDING | Zone `208681448c90a193489a0907a48f6166`, NS: `jonah.ns.cloudflare.com`, `kiki.ns.cloudflare.com` |
| DNS apex (concerto.run) | ✅ configured | A → `204.168.130.247` (VPS IP — needs update to Vercel target post-deployment) |
| DNS api.concerto.run | ✅ configured | CNAME → tunnel `27603591-aed3-4aa2-a722-d4a6d34a44f4.cfargotunnel.com` |
| DNS install.concerto.run | ✅ configured | CNAME → same tunnel |
| DNS status.concerto.run | ❌ MISSING | No record configured |
| Tunnel ingress: api.concerto.run | ✅ PASS | → `http://127.0.0.1:8090` |
| Tunnel ingress: install.concerto.run | ✅ PASS | → `http://127.0.0.1:8090` |
| Tunnel ingress: api.maestro.run | ⚠️ STALE | Still present — remove after confirming no maestro.run customers |

**NS update command** (NameSilo operator):
> Log into NameSilo → concerto.run → Manage DNS → Remove current NS → Set to `jonah.ns.cloudflare.com` + `kiki.ns.cloudflare.com`

---

## G. Emails

| Check | Status | Detail |
|-------|--------|--------|
| Transactional templates (4) | ✅ PASS | HTML valid: `provisioning_complete`, `provisioning_failed`, `purchase_confirmation`, `welcome_after_first_session` |
| Drip templates (7) | ✅ PASS | HTML valid: day 0/1/3/7/14/21/30 |
| Dynamic variables | ⚠️ INFO | Templates use `{{email_url}}`, `{{setup_url}}`, `{{dashboard_url}}` etc. — runtime replacements; backend must provide all values |
| Resend `concerto.run` domain | ❌ MISSING | Only `strandedgrid.com` verified. Without `concerto.run` in Resend, all transactional emails will fail or fall back to `strandedgrid.com` sender |
| email invite URL | ⚠️ NOT SET | `SUPPORT_EMAIL_URL` env var missing — templates reference `{{email_url}}` |

---

## H. Documentation

| Document | Status |
|----------|--------|
| README.md | ✅ present, 8 Concerto refs, install instructions |
| docs/ARCHITECTURE.md | ✅ present, 11 refs |
| docs/SECURITY.md | ✅ present, 17 refs |
| docs/FAQ.md | ✅ present, 9 refs |
| docs/ROADMAP.md | ✅ present, 6 refs |
| docs/RUNBOOK.md | ✅ present (PR #24), 96 refs |
| docs/COMPETITIVE_MATRIX.md | ✅ present, 6 refs |
| docs/PRODUCT_BRIEF.md | ✅ present, 14 refs |
| docs/CUSTOM_STYLE.md | ✅ up to date (orchestral metaphor, "soloist + fleet") |
| docs/legal/TERMS.md | ✅ present |
| docs/legal/PRIVACY.md | ✅ present |
| docs/legal/REFUND.md | ✅ present |
| docs/legal/AUP.md | ✅ present |

---

## I. Operator Action Queue (Ranked)

### 🔴 LAUNCH BLOCKERS — operator must do before any sales

| # | Action | Why Blocking |
|---|--------|-------------|
| 1 | **NameSilo: update NS to Cloudflare** (`jonah.ns.cloudflare.com`, `kiki.ns.cloudflare.com`) | Zone status `pending` — concerto.run resolves to nothing |
| 2 | **Register Stripe webhook** at `https://api.concerto.run/webhooks/stripe-concerto`, listen for `checkout.session.completed`, `customer.subscription.*`; copy signing secret to `/etc/cortex/env` as `STRIPE_CONCERTO_WEBHOOK_SECRET` + restart concerto-backend | All purchases will process but webhook handler rejects events → no provisioning |
| 3 | **Resend: add `concerto.run` domain**, add DKIM/SPF records in Cloudflare DNS, verify | All transactional emails fail (welcome, provisioning, drip) |
| 4 | **Set `CONCERTO_DO_API_TOKEN`** in `/etc/cortex/env` (rename from old `MAESTRO_DO_API_TOKEN` key or use DigitalOcean PAT) + `systemctl restart concerto-backend.service` | Hosted plan provisioning fails silently |
| 5 | **Vercel: import `ethanadjedj-labs/concerto`**, set custom domain `concerto.run`, add env vars (`NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`, `CONCERTO_DO_API_TOKEN`, `STRIPE_SECRET_KEY`, `STRIPE_CONCERTO_PRICE_ID`, `STRIPE_CONCERTO_HOSTED_PRICE_ID`, `STRIPE_CONCERTO_WEBHOOK_SECRET`, `RESEND_API_KEY`, `BACKEND_URL=https://api.concerto.run`); update Cloudflare apex A record to Vercel target | Frontend only accessible via unstable trycloudflare preview URL |

### 🟡 RECOMMENDED — can launch soft without, but should do within 48h

| # | Action |
|---|--------|
| 6 | **Start concerto timers**: `systemctl start concerto-hosted-lifecycle.timer concerto-drip-runner.timer concerto-status-writer.timer concerto-monitoring.timer` |
| 7 | **Create status dir**: `mkdir -p /var/www/concerto-status && chown www-data:www-data /var/www/concerto-status` → starts writing `status.json` |
| 8 | **Add `status.concerto.run`** Cloudflare DNS CNAME → Vercel (or tunnel), + add ingress rule to tunnel |
| 9 | **Set `SUPPORT_EMAIL_URL`** in `/etc/cortex/env` (create email server first) |
| 10 | **Stripe Tax**: log into Stripe → Tax → Settings → set head_office location → enable automatic tax collection on Concerto products |
| 11 | **Remove `api.maestro.run`** from tunnel ingress after confirming zero maestro.run active sessions |
| 12 | **Rebuild + restart frontend preview** from latest repo code: `cd /tmp/concerto-audit/frontend && npm run build && pkill -f "next start" && nohup npm start -- -p 3500 > /tmp/concerto-next.log 2>&1 &` |

---

## Auto-Fixes Applied

1. **`.gitignore`**: added `*.db` and `*.db.backup` entries
2. **`frontend/.eslintrc.json`**: created with `{"extends": ["next/core-web-vitals"]}` — `npm run lint` now passes with 0 warnings/errors

---

## RAM Observed

- **VPS total**: 15,982 MB
- **VPS available during audit**: ~13,000–13,900 MB (well above 300 MiB abort threshold)
