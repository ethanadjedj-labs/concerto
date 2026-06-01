> **→ Superseded by /opt/infra/skills/stripe-multibrand/SKILL.md** (canonical, verified live 2026-06-01). This file is retained for historical context only.

# Stripe topology — empire (concerto + clickcure)

Snapshot: 2026-05-31. Discovery output for WS3 Stripe multi-brand work.
Source of truth: this file lives in `concerto/docs/` and is referenced
by clickcure (see `clickcure/docs/stripe_topology.md`).

## TL;DR

Today the empire has **ONE shared Stripe platform account**. Both
Concerto (subscriptions) and ClickCure (one-time Express £300) bill
through it. The hosted Stripe Checkout page therefore shows
"Concerto" on the ClickCure payment flow — bad for ClickCure trust
and ambiguous for accounting.

WS3 introduces a **Stripe Connect (Standard) layer**: the platform
account stays where it is, and each brand becomes a **connected
account** under it. All checkout sessions are then created
server-side with `stripe_account=<connected_account_id>`, so the
hosted checkout, statement_descriptor and payouts inherit the
connected account's identity.

## Brands

| Brand | Domain | Product | Pricing | Currency | Statement descriptor (target) |
|---|---|---|---|---|---|
| Concerto | `concerto.run` | Managed Claude Code hosting (subscription: solo + pro) | recurring | USD | `CONCERTO.RUN` |
| ClickCure | `clickcure.co` | Express £300 — UK dental landing page (one-time) | one-time | GBP | `CLICKCURE.CO` |

Concerto is the **default brand** for backwards compatibility — its
existing Stripe flows MUST stay byte-for-byte identical on the wire
until/unless an operator explicitly migrates it onto a connected
account. The "shared account" referred to above is, after WS3,
re-described as "the Concerto brand on the platform account with no
`stripe_account` override". That keeps live revenue untouched.

ClickCure is a **new connected account** to be created in the Stripe
dashboard (KYC required — see `stripe_multibrand_runbook.md`). Until
the operator finishes onboarding and pastes the
`connected_account_id` into config, the ClickCure checkout endpoint
will **fail loudly** rather than fall back to the Concerto-branded
link. The hardcoded `buy.stripe.com/cNidR882…` link is removed.

## Existing Stripe touchpoints — Concerto

All in `/opt/concerto`.

### Backend (Python, FastAPI)

| File | Role | Notes |
|---|---|---|
| `backend/concerto/stripe_webhook.py` | `/webhooks/stripe-concerto` — receives `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.*`, `charge.dispute.created` | Signature-verified, idempotent claim/done state machine. Filters by `metadata.product == "concerto"`. |
| `backend/concerto/customer_portal.py` | Billing portal session, cancel-by-link, cancel-by-email | Uses `stripe.billing_portal.Session.create`, `stripe.Subscription.list/modify`. |
| `backend/concerto/status_router.py` | `/api/buyer/{token}/cancel` | `stripe.Subscription.cancel`. |
| `backend/concerto/refunds.py` | Operator refund flow | `stripe.checkout.Session.retrieve` + `stripe.Refund.create`. |

### Frontend (Next.js)

| File | Role | Notes |
|---|---|---|
| `frontend/app/api/checkout/route.ts` | Public checkout entry point — `stripe.checkout.sessions.create` (subscription mode) | Reads `STRIPE_CONCERTO_SOLO_PRICE_ID` / `STRIPE_CONCERTO_PRO_PRICE_ID`. Hard-codes `metadata.product = "concerto"`. |
| `frontend/.env.local.example` | `STRIPE_SECRET_KEY`, `NEXT_PUBLIC_STRIPE_PUBLIC_KEY`, `STRIPE_CONCERTO_*_PRICE_ID` | |
| Various `.tsx` mention `stripe` in marketing copy only — non-functional | |

### Env vars (Concerto today)

- `STRIPE_SECRET_KEY` — platform-account secret key (used by both backend and Next.js api route).
- `STRIPE_CONCERTO_WEBHOOK_SECRET` — webhook signing secret for `/webhooks/stripe-concerto`.
- `STRIPE_CONCERTO_SOLO_PRICE_ID`, `STRIPE_CONCERTO_PRO_PRICE_ID` — concerto subscription prices.
- `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` — frontend publishable key.

None of these change in WS3. Concerto remains the default brand on
the platform account, with no Connect routing applied.

## Existing Stripe touchpoints — ClickCure

All in `/opt/clickcure`.

| File | Role | Status |
|---|---|---|
| `verticals/dental_uk/site/index.html` (line 247) | Hardcoded `<a href="https://buy.stripe.com/cNidR882uaZ5aPB59g8k805">` — Concerto-shared payment link | **REPLACED in WS3** with `/checkout` server-side endpoint. |
| `core/web_server.py` (lines 89-92, 392-393, 500) | Click tracker auto-tags `<a href="https://buy.stripe.com/...">` as `stripe_click` for funnel metrics | Stays — pattern still matches the new Checkout Session URL when emitted server-side. |
| `core/agents/seller.py`, `core/demo_template_v5.py`, `core/competitive_report.py` | Read `pricing[*].stripe_link` from per-prospect config — used in demo pages emitted to prospects | Stays. The `stripe_link` field is now populated from the brand config (`make_checkout_url("clickcure", ...)` materialises a Checkout Session url server-side). |

There is **no Stripe SDK use in ClickCure backend today** — the
entire server-side integration is new code added in WS3.

## After WS3 — runtime call shape

### Concerto (unchanged)

```python
# backend (Python) — refund / subscription / customer portal
stripe.api_key = STRIPE_SECRET_KEY
stripe.Refund.create(payment_intent=..., reason="requested_by_customer")
# NO stripe_account override
```

```ts
// frontend Next.js — /api/checkout
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: "2025-02-24.acacia" })
await stripe.checkout.sessions.create({ ... metadata: { product: "concerto", ... } })
// NO stripe_account override
```

This is exactly today's behaviour. Adding the brand layer does not
introduce a `stripe_account=` kwarg for the `concerto` brand.

### ClickCure (new)

```python
# clickcure backend — new /checkout endpoint
brand = brand_stripe.get_brand("clickcure")  # raises if connected_account_id missing
stripe.api_key = STRIPE_SECRET_KEY  # platform secret
stripe.checkout.Session.create(
    line_items=[{"price": brand.express_price_id, "quantity": 1}],
    mode="payment",
    payment_intent_data={"statement_descriptor": brand.statement_descriptor},
    success_url=..., cancel_url=...,
    metadata={"product": "clickcure", "vertical": "dental_uk", ...},
    stripe_account=brand.connected_account_id,  # routes hosted checkout to ClickCure account
)
```

The session URL is then surfaced as the value the static site / demo
templates fetch instead of `buy.stripe.com/...`.

### Webhooks after WS3

Concerto keeps `/webhooks/stripe-concerto` filtering on
`metadata.product == "concerto"`. ClickCure adds (out of WS3 scope,
referenced for completeness in the runbook) `/webhooks/stripe-
clickcure` once the connected account is wired up — webhooks from
a connected account are delivered as Connect events with an
`account` field; the new endpoint will accept them and update the
clickcure SQLite store. This is the next sprint's slice.

## Cross-repo contracts (brand config)

A minimal `brands.toml` config is duplicated in each repo (the empire
contract bans cross-product imports; clickcure may only import
`arsenal.*` and `core.*`). Both copies follow the same schema:

```toml
# brands.toml — concerto copy under backend/concerto/, clickcure copy under core/
[brands.concerto]
display_name = "Concerto"
domain = "concerto.run"
support_email = "support@concerto.run"
statement_descriptor = "CONCERTO.RUN"
currency = "usd"
connected_account_id = ""   # empty = use platform account directly (today's behaviour)

[brands.clickcure]
display_name = "ClickCure"
domain = "clickcure.co"
support_email = "contact@clickcure.co"
statement_descriptor = "CLICKCURE.CO"
currency = "gbp"
# TODO(operator): paste acct_xxx after Stripe Connect onboarding
# (see docs/stripe_multibrand_runbook.md)
connected_account_id = ""
express_price_id = ""        # TODO(operator): create one-time price for £300 in the ClickCure connected account
```

Loader contract: `load_brands()` parses the TOML, validates that
unknown brands raise, and exposes `make_stripe_session_kwargs(brand)`
that returns `{"stripe_account": id}` when `connected_account_id` is
non-empty, and `{}` otherwise. The `{}` path is what preserves the
Concerto default behaviour.

## Risk matrix

| Risk | Likelihood | Mitigation |
|---|---|---|
| Accidentally route a Concerto checkout to a Connect account before onboarding | Low | `connected_account_id = ""` for concerto in shipped config; loader returns `{}` so call shape is unchanged; regression test asserts no `stripe_account` kwarg appears on the wire for `metadata.product=concerto`. |
| ClickCure checkout silently falls back to the shared Concerto link | Medium | Removed the hardcoded `buy.stripe.com` URL from the HTML; the new endpoint raises `HTTPException(503, "ClickCure Stripe Connect not configured")` when `connected_account_id` is empty. No fallback. |
| Live keys used in tests | Low | Both test suites set `STRIPE_SECRET_KEY=sk_test_dummy` before importing modules; the stripe SDK is mocked in every test that touches a `.create` call. |
| KYC takes days; operator wants to ship sooner | Medium | The clickcure endpoint code is shipped behind a "Stripe Connect not configured" hard failure. UX during the gap: the landing CTA reverts to a contact-form-only path. See runbook §rollback. |

## Files added / changed by WS3

### concerto branch `claude/stripe-multibrand-platform`

- `docs/stripe_topology.md` (this file)
- `docs/stripe_multibrand_runbook.md`
- `backend/concerto/brand_stripe.py` — TOML loader + `make_stripe_session_kwargs`
- `backend/concerto/brands.toml` — concerto brand defaults; clickcure entry kept here for visibility but consumed by the clickcure repo's copy
- `backend/tests/test_brand_stripe.py` — regression test (concerto unchanged, clickcure routed)
- `docs/PRODUCTION_READINESS.md` — note new module + green test

### clickcure branch `claude/stripe-multibrand-clickcure`

- `docs/stripe_topology.md` — cross-link to the concerto copy + clickcure-specific notes
- `core/brand_stripe.py` — same schema as concerto copy
- `core/brands.toml` — clickcure brand config (TODOs for KYC values)
- `core/checkout_endpoint.py` — new server-side handler + integration into `core/web_server.py`
- `verticals/dental_uk/site/index.html` — replace hardcoded `buy.stripe.com` link with relative `/checkout?brand=clickcure&plan=express` POST
- `tests/test_brand_stripe.py` — endpoint fails loudly when `connected_account_id` empty; succeeds + emits correct kwargs when set
- `CAPABILITIES.md` and `docs/PRODUCTION_READINESS.md` — note new module
