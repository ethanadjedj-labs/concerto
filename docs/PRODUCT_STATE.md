# Concerto — Real Product State

*Snapshot date: 2026-06-03 — source of truth: `/var/lib/concerto/concerto.db`.*

This document records the **honest** state of the product: real users, real
provisions, real sessions. Nothing is invented. Every number below is
reproducible with a `sqlite3` query against the production SQLite. The
in-repo `backend/concerto.db` is a 0-byte placeholder; the live DB path
is `CONCERTO_DB_PATH=/var/lib/concerto/concerto.db` (see
`backend/concerto/db.py`).

---

## TL;DR

The funnel **does deliver** end-to-end for a real user (paid →
provisioned → installed → first MCP call), most recently exercised
**2026-06-03 12:14 → 12:23 UTC** by the operator's own self-test trial.
There are **no external paying customers yet**: zero rows in
`concerto_buyers` outside that one trial, zero non-test rows in
`stripe_processed_events`. Nothing is in a stuck/errored state.

## 1. Buyer table — every row

```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT status, plan, COUNT(*) FROM concerto_buyers GROUP BY status, plan;"
```

| status         | plan  | rows |
|----------------|-------|------|
| `trial_expired`| trial | 1    |
| **total**      |       | **1** |

The single row is the operator (`adjedjethan@gmail.com`, matched by
`_OPERATOR_EMAIL_RE` in `backend/concerto/trial_router.py:20`). Treat it
as a completed self-test, not as an arms-length customer.

**Real paying customers:** 0.
**Real trials by external emails:** 0.
**Buyer rows in failed states** (`provisioning_failed`, `failed_install`,
`api_key_invalid`, `account_no_credit`, `provisioning_timeout`,
`suspended`, `refunded`): 0.

## 2. End-to-end funnel for that single buyer

```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT datetime(paid_at,'unixepoch'),
          datetime(provisioned_at,'unixepoch'),
          datetime(installed_at,'unixepoch'),
          datetime(first_call_at,'unixepoch'),
          status, failure_reason
   FROM concerto_buyers;"
```

| step                | timestamp (UTC)       | Δ since previous |
|---------------------|-----------------------|------------------|
| `paid_at`           | 2026-06-03 12:14:50   | —                |
| `provisioned_at`    | 2026-06-03 12:15:43   | +53 s            |
| `installed_at`      | 2026-06-03 12:15:44   | +1 s             |
| `first_call_at`     | 2026-06-03 12:23:08   | +7 m 24 s        |
| trial expiry        | 2026-06-03 14:14:50   | +2 h             |

`failure_reason` is NULL. The 7-minute gap before `first_call_at`
reflects a real user walking through OAuth in the browser, not a bug.

**Conclusion: the core promise — pay → Claude-Code-on-your-cloud → first
MCP call — is observed working today on production via the Northflank
provider.**

## 3. Lifecycle events (engagement signal)

```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT event_type, source, COUNT(*)
   FROM concerto_lifecycle_events GROUP BY event_type, source;"
```

| event_type | source           | count |
|------------|------------------|-------|
| `resume`   | `mcp_proxy_wake` | 4     |
| `pause`    | `auto_pause`     | 2     |

Six events spanning 2026-05-21 → 2026-06-03, all tied to the operator's
environment. The auto-pause + wake-on-call lifecycle (commit `e27309e`)
is firing as designed — the env idle-pauses, the proxy wakes it on the
next MCP call.

## 4. Hosted pool (Northflank)

```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT droplet_id, status,
          datetime(created_at,'unixepoch'),
          datetime(destroyed_at,'unixepoch')
   FROM concerto_hosted_pool;"
```

| droplet_id          | status      | created             | destroyed           |
|---------------------|-------------|---------------------|---------------------|
| `concerto-pqyhhckm` | `destroyed` | 2026-05-17 06:23 Z  | 2026-06-02 18:21 Z  |

One historical Northflank service, cleanly destroyed. **Zero orphans.**

## 5. Stripe webhook idempotency log

```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT event_id FROM stripe_processed_events
   WHERE event_id NOT LIKE 'evt_test_%' AND event_id NOT LIKE 'evt_qa_%';"
-- → evt_noproduct_1779088431
-- → evt_idempotency_test_1779088454
-- → evt_emailfix_test_1779100566
```

The narrow `NOT LIKE` filter returns 3 rows but inspection shows all 3
are themselves QA fixtures from the 2026-05-17/05-18 hardening sweep,
just with non-uniform naming (`evt_noproduct_*`, `evt_idempotency_test_*`,
`evt_emailfix_test_*`). The remaining 14 rows match the
`evt_test_solo_e2e_*` / `evt_qa_solo_*` / `evt_qa_pro_*` shapes. No
real Stripe-issued event ID (which would start with `evt_[0-9]`) is
present. Zero real checkouts have hit the webhook yet.

`/api/admin/product-metrics` reports `stripe.events_real = 3` because
its filter is purely the `NOT LIKE 'evt_test_%' / 'evt_qa_%'`
heuristic — see the discrepancy noted in `docs/DEPTH_PROOF.md` §1. The
honest interpretation is: the endpoint flag means "event ID does not
match the two most common QA prefixes", not "originated from a real
Stripe charge".

## 6. OAuth failures

```
sqlite3 /var/lib/concerto/concerto.db "SELECT COUNT(*) FROM concerto_oauth_failures;"
-- → 0
```

Zero recorded OAuth failures. The F-01 → F-13 hardening (commits
`252a30f`, `35e5520`, `064b733`) holds — no buyer has hit the failure
table since it was added.

## 7. Email dead-letter — the one historical gap

```
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT MIN(datetime(attempted_at,'unixepoch')),
          MAX(datetime(attempted_at,'unixepoch')),
          COUNT(*)
   FROM concerto_email_dead_letter;"
```

| earliest               | latest                 | rows |
|------------------------|------------------------|------|
| 2026-05-17 17:59 UTC   | 2026-05-18 07:34 UTC   | 15   |

All 15 rows are from a 14-hour QA burst on 2026-05-17/18 that tripped
Migadu's `4.7.0 too many errors` rate limit; every `to_addr` is
`adjedjethan+<qa-tag>@gmail.com` or `*@test.com`. No real customer
email has ever dead-lettered. Since `34b662d` (mailroom integration
with criticality routing + audible fallback), critical-path mail
(trial-ready, welcome, refund confirmation) goes through the mailroom;
nothing has dead-lettered since.

## 8. What this state means for next investment

The funnel is plumbed end-to-end and observed green on production today,
but the only user is the operator. Therefore the highest-leverage work
is **not** "scale this up" — it is:

1. Keep failure paths fail-closed + auto-refunded (audited in
   `docs/DEPTH_PROOF.md` §2).
2. Make the very first real customer's metrics visible to the operator
   the moment they arrive (the `/api/admin/product-metrics` endpoint
   added in this PR queries the buyer/lifecycle/Stripe/oauth tables
   directly — there is no in-memory counter to drift).
3. Do not invent numbers. If a count cannot be derived from the
   production DB, it does not appear here or in the metrics endpoint.

See `docs/DEPTH_PROOF.md` for the structured proof.
