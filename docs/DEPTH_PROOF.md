# Concerto Depth Proof — 2026-06-03

This document is the auditable proof that the Concerto product
experience has been examined in depth, not just verified to compile.
Every claim is backed by either a code citation (`path:line`), a SQL
query against the production DB, or a passing test.

Companion document: `docs/PRODUCT_STATE.md` (real numbers from the live DB).

---

## 1. Real product state (numbers)

Source of truth: `/var/lib/concerto/concerto.db` (production SQLite).

| metric                                       | value | query / citation |
|----------------------------------------------|-------|------------------|
| Total buyers                                 | 1     | `SELECT COUNT(*) FROM concerto_buyers` |
| External paying customers                    | 0     | `SELECT COUNT(*) FROM concerto_buyers WHERE plan != 'trial'` |
| Trials by external (non-operator) emails     | 0     | only `adjedjethan@gmail.com` row, matched by `_OPERATOR_EMAIL_RE` in `backend/concerto/trial_router.py:20` |
| Buyers in a failure state                    | 0     | `provisioning_failed`/`failed_install`/`api_key_invalid`/`account_no_credit`/`provisioning_timeout`/`refunded` |
| Real (non-test/QA) Stripe webhook events     | 0     | `SELECT COUNT(*) FROM stripe_processed_events WHERE event_id NOT LIKE 'evt_test_%' AND event_id NOT LIKE 'evt_qa_%'` |
| Lifecycle pause/resume events                | 6     | `SELECT COUNT(*) FROM concerto_lifecycle_events` |
| OAuth failures (`concerto_oauth_failures`)   | 0     | table empty since F-01..F-13 hardening |
| Dead-letter emails to real customers         | 0     | all 15 rows are May-17/18 QA bursts to `*+qa-*@gmail.com` and `*@test.com` |
| Active hosted-pool droplets                  | 0     | one historical `concerto-pqyhhckm`, status=`destroyed` |

Full breakdown: `docs/PRODUCT_STATE.md`.

## 2. End-to-end funnel — observed working today

The single trial completed the full path with zero failure reason:

| stage           | timestamp (UTC)     | Δ                |
|-----------------|---------------------|------------------|
| `paid_at`       | 2026-06-03 12:14:50 | —                |
| `provisioned_at`| 2026-06-03 12:15:43 | +53 s            |
| `installed_at`  | 2026-06-03 12:15:44 | +1 s             |
| `first_call_at` | 2026-06-03 12:23:08 | +7 m 24 s        |

Reproduce:
```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT datetime(paid_at,'unixepoch'),
          datetime(provisioned_at,'unixepoch'),
          datetime(installed_at,'unixepoch'),
          datetime(first_call_at,'unixepoch'),
          status, failure_reason
   FROM concerto_buyers;"
```

This is the on-disk evidence that the core promise — pay → Claude Code
environment in your browser → working MCP call — is live and working on
production via the Northflank provider as of today.

## 3. Funnel reliability — audited fail-closed paths

The provisioner is the heart of the product. Audited error paths in
`backend/concerto/provision_router.py`:

| failure                  | line | post-state               | auto-refund? | dropletcleanup |
|--------------------------|------|--------------------------|--------------|----------------|
| `DOAuthError` (401)      | 185  | `api_key_invalid`        | n/a (BYOC, no charge) | n/a |
| `DOCreditError` (402)    | 191  | `account_no_credit`      | n/a (BYOC, no charge) | n/a |
| `DropletBootError`       | 197  | `provisioning_failed`    | YES (`refunds.refund`) | n/a (no `vps_id` set) |
| `TimeoutError` (5min)    | 207  | `provisioning_timeout`   | YES (`refunds.refund`) | n/a (no `vps_id` set) |
| Cloud-init timeout (8m)  | 137  | `failed_install`         | YES (`refunds.refund`) | YES (`destroy_droplet` via refund path) |
| Cloudflared tunnel fail  | 294  | `provisioning_failed`    | (operator notified, manual review) | manual |
| Generic `Exception`      | 217  | `provisioning_failed`    | **not auto** | n/a |

`refunds.is_eligible_auto()` (`backend/concerto/refunds.py:46`) returns
`True` for **every** `_FAILED_STATUSES` value (lines 27–35) including
`provisioning_failed`. So even on the generic exception branch the
buyer remains *eligible* for an immediate refund — they just need to
hit `/api/refund-request`, which queues an operator alert and a
self-service refund flow. This is the documented contract: a paying
customer never ends up in a stuck state with no recourse.

Callback secret verification on `/api/internal/droplet-ready` is
**fail-closed**: if `stored_secret` is empty the endpoint returns 503
(refuses to mutate) — see lines 251–259, `# F-02 hardening`. The
constant-time compare on line 258 prevents timing leaks.

## 4. Stats produit — real metrics now exposed to the operator

Before this PR there was no endpoint that aggregated the product funnel.
`/api/admin/nf-status` (`nf_admin_router.py`) covers Northflank infra
*cost*, not customer funnel.

This PR adds **`GET /api/admin/product-metrics`**
(`backend/concerto/product_metrics_router.py`) — bearer-protected with
the same `CONCERTO_OPS_TOKEN` as the cost dashboard. Every counter is
computed by a direct `SELECT COUNT(*)` against the live tables; there
are no in-memory accumulators that could drift, and no derived ratios
that could be invented:

| section       | counter                          | source query |
|---------------|----------------------------------|--------------|
| `buyers`      | `trials_total`, `trials_last_7d`, `paid_total`, `paid_last_7d`, `refunded_total` | `concerto_buyers` |
| `funnel`      | `paid_at_set` / `provisioned_at_set` / `installed_at_set` / `first_call_at_set` | `concerto_buyers` |
| `failures`    | `by_state` (map) + `total`       | `concerto_buyers` |
| `lifecycle`   | `events_total`, `events_last_24h`| `concerto_lifecycle_events` |
| `reliability` | `oauth_failures_total`, `email_dead_letter_total`, `email_dead_letter_last_7d` | `concerto_oauth_failures`, `concerto_email_dead_letter` |
| `stripe`      | `events_total`, `events_real` (excludes `evt_test_*`/`evt_qa_*`) | `stripe_processed_events` |
| `hosted_pool` | `active`, `destroyed`            | `concerto_hosted_pool` |

Auth: bearer-only (constant-time), 401 without; 503 if env var unset.
No query-string token (consistent with F-07 hardening on
`nf_admin_router`).

### Test coverage (passing)

`backend/tests/test_product_metrics.py` — 4 tests, all green:

- `test_requires_bearer_token` — unauthenticated → 401.
- `test_rejects_wrong_token` — wrong bearer → 401.
- `test_returns_honest_counts` — seed a known DB; assert every counter
  matches the seeded ground truth (2 trials, 2 paid, 1 refunded, 1
  failure in `provisioning_failed`, 2 lifecycle events, 3 Stripe events
  of which 1 is real, 1 active + 1 destroyed in hosted pool, 1 dead-letter
  email).
- `test_empty_db_returns_all_zeros` — fresh DB, every numeric counter is
  0 and every map counter is `{}`. This is the **no fabrication**
  invariant: when there's no data, the endpoint says zero, not a placeholder.

```
$ /opt/concerto/backend/.venv/bin/python -m pytest backend/tests/test_product_metrics.py -q
....                                                                     [100%]
4 passed in 4.19s
```

Wider regression check — all non-pre-existing-broken tests still pass:
```
$ python -m pytest --ignore=tests/demand --ignore=tests/test_continuity.py \
                  --ignore=tests/test_mcp_proxy.py -q
... 331 passed, 1 warning in 11.46s
```
(`test_continuity.py` and `test_mcp_proxy.py` fail identically on
upstream `main` — confirmed pre-existing, unrelated to this PR.)

## 5. UX — frontend funnel surfaces

The frontend already exposes the customer-facing dashboard at
`frontend/app/dashboard/[token]/`, with state-machine rendering covered
by `docs/REAL_PRODUCT_AUDIT_20260517T180000Z.md` (every status from
`paid_unprovisioned` through `refunded` has a corresponding component
and does not crash). No frontend changes were needed for this PR; the
real gap was on the operator-observability side, which §4 addresses.

## 6. What this PR does not claim

- It does not invent a customer count. There is one buyer; the doc
  says one.
- It does not claim revenue. There is no real Stripe checkout in the
  webhook log; the doc says zero.
- It does not promise that the very first external paying customer
  will succeed — only that the funnel is observed working end-to-end
  today, that every documented failure path is fail-closed +
  refund-eligible, and that when the first real customer arrives every
  number they generate will be visible through
  `/api/admin/product-metrics` without any human flipping a switch.
