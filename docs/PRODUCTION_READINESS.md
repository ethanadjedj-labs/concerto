# concerto — production readiness

Status as of the empire production-bar sweep
(goal `0648ad8a-78d0-4d69-b17a-14d6e9f50ac8`, 2026-05-31).

## Verdict: **YELLOW (hybrid python+node, top-level gate N/A)**

concerto is a **hybrid** repo: `backend/` is a Python FastAPI service
(managed Claude Code hosting, `concerto.run`), `frontend/` is a Next.js
app. The python conformance gate runs at the top level, where there
is no `pyproject.toml` — the gate's `[b]` step therefore fails
structurally. Run the gate against `backend/` instead.

| Bar | Status | Evidence |
|---|---|---|
| **B1 tests** | ⚠ deferred | Backend pytest suite present at `backend/tests/` (test_cancel_by_email, test_trial_*, test_oauth_*, test_terminal_router, test_hosted_lifecycle_unit, …). Not part of the sweep harness top-level pytest. Run `cd backend && python -m pytest -q` to verify |
| **B2 conformance gate** | ⚪ N/A top-level | Run `bash /opt/infra/ops/conformance_gate.sh --repo /opt/concerto/backend --ref main` to gate the backend. Frontend has its own `next build` check |
| **B3 CLAUDE.md** | ⚠ stale | Top-level `CLAUDE.md` (23 lines) is the legacy cortex-era spawn instructions; refers to retired `/var/lib/cortex/cortex.db`. Needs rewrite as the proper Part-A/Part-B operating directive |
| **B4 dead code** | — | Deferred until B2 + B3 settled |
| **B5 branch hygiene** | ⚠ | Multiple `claude/concerto-*` topic branches present; reap planned |
| **B6 README aligned** | ⚠ thin | `README.md` (19 lines) describes the workspace concept but not the concerto.run product surface |
| **B7 readiness doc** | ✓ | this file |

## Surface

- **Backend** (`backend/`): FastAPI + Stripe + arsenal. Modules under
  `backend/concerto/` (separate from top-level `concerto/` legacy dir).
  Tests under `backend/tests/`.
- **Frontend** (`frontend/`): Next.js 16, Radix UI components, hosted
  on Next runtime. Standard `npm run build`.
- **Skill package** (`skill-package/`): Concerto skill artefact
  consumed by claude.ai integration.
- **Installer** (`installer/`): Claude Code install + bootstrap helper.

## Open follow-ups

1. Rewrite top-level `CLAUDE.md` as a Part-A/Part-B identity card (current text is the legacy spawn instructions; obsolete since the cortex → empire migration).
2. Add a top-level umbrella `pyproject.toml` (or document that the gate must be run against `backend/`) so the python conformance gate has a defined target.
3. Expand `README.md` to describe the product (managed Claude Code hosting, concerto.run) rather than the workspace concept only.

## WS3 Stripe multi-brand (2026-05-31)

Shipped on this branch: `backend/concerto/brand_stripe.py` +
`backend/concerto/brands.toml` add a brand-aware Stripe Connect
routing layer. **Concerto stays on the platform account
unchanged** — for `brands.concerto.connected_account_id = ""` the
helper returns `{}` kwargs and every existing call site behaves
byte-for-byte identically to today. Regression guarded by
`backend/tests/test_stripe_concerto_regression.py` (Stripe brand
suite: 17 tests pass; existing `test_stripe_idempotency.py` 9 tests
still green; full backend pytest baseline noise on
`test_continuity.py` / `test_mcp_proxy.py` is unrelated to WS3 and
pre-existed on `origin/main`).

ClickCure consumer side ships on
`clickcure/claude/stripe-multibrand-clickcure`. Operator runbook
for the manual Stripe-dashboard steps that finish the migration:
`docs/stripe_multibrand_runbook.md`.

## Re-running the bar

```bash
# Backend B1
cd /opt/concerto/backend && python -m pytest -q
# Backend B2 (alt target)
bash /opt/infra/ops/conformance_gate.sh --repo /opt/concerto/backend --ref main
# Frontend (Node)
cd /opt/concerto/frontend && npm ci && npm run build
```
