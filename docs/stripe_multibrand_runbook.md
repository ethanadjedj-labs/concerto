> **→ Superseded by /opt/infra/skills/stripe-multibrand/SKILL.md** (canonical, verified live 2026-06-01). This file is retained for historical context only.

# Stripe multi-brand runbook (Concerto + ClickCure)

Operator-facing manual steps to finish the WS3 multi-brand
migration. The code side is shipped on branches
`concerto/claude/stripe-multibrand-platform` and
`clickcure/claude/stripe-multibrand-clickcure`. The steps below are
the ones that **must be done in the Stripe dashboard** — they cannot
be automated because they require KYC, identity verification, and a
human acknowledging legal terms.

Audience: Ethan (or any portfolio operator).
Estimated wall-clock: 30–45 min of clicking + 1–3 business days
waiting on Stripe identity review.

---

## 0. Before you start

- Sign in to the empire Stripe **platform** account at
  <https://dashboard.stripe.com> (the same account that today owns
  the Concerto subscriptions and the `cNidR882…` ClickCure Payment
  Link).
- Have ready: ClickCure legal name, registered address, bank account
  for ClickCure payouts, business website (`clickcure.co`).
- Keep this runbook open in another tab.

> ⚠ **Do nothing in the platform's "Live" mode if you are not sure.**
> Every step below is safe to dry-run in Stripe's "Test mode" first
> (top-right toggle). The connected-account-id you'll paste into
> `brands.toml` differs between test and live; ship one branch at a
> time.

---

## 1. Enable Stripe Connect on the platform

> Goal: make the platform account capable of holding **connected
> accounts**. Today it isn't.

1. Go to **Settings → Connect** in the Stripe dashboard.
   <https://dashboard.stripe.com/settings/connect/onboarding-options>
2. Click **Get started** if Connect has never been enabled.
3. Pick the **Platform or marketplace** preset.
4. **Type of accounts**: select **Standard**.
   - Why Standard (not Express or Custom):
     - Standard gives the connected-account holder a full Stripe
       dashboard. ClickCure has its own KYC, branding,
       statement_descriptor and payouts that the operator controls
       from a separate dashboard. No platform-side UI to build.
     - Express would require us to host an onboarding flow ourselves;
       wasted effort for a single-operator portfolio.
     - Custom is API-only and puts every compliance obligation on the
       platform — overkill for our scale.
5. **Application name** shown to users during onboarding: `Empire`
   (or your preferred portfolio name).
6. **Application icon**: optional. Upload one if you want a branded
   onboarding screen — does NOT affect the connected account's own
   branding.
7. Save. Stripe activates Connect immediately; you'll see a new
   **Connected accounts** tab in the dashboard.

> 🚦 **Concerto sanity check after this step**: Concerto's existing
> subscriptions, webhooks, refunds and customer portal sessions
> continue to work unchanged. Enabling Connect is a platform-level
> capability — it does **not** alter how the platform account
> handles direct charges. The regression test
> `backend/tests/test_stripe_concerto_regression.py` proves the
> call shape stays empty-kwargs.

---

## 2. Create the ClickCure connected account

1. **Connect → Connected accounts → + Create**.
2. Choose **Standard**.
3. **Account email**: `contact@clickcure.co` (or your owner email).
4. **Country**: `United Kingdom`.
5. Send the onboarding invitation. Stripe emails the account a link
   to finish KYC (see §3 below).
6. Immediately after creation, the connected account has an id of
   the form `acct_xxxxxxxxxxxxxxxxxx`. Copy it.
7. Paste it as a temporary value in BOTH
   `/opt/concerto/backend/concerto/brands.toml` AND
   `/opt/clickcure/core/brands.toml` under
   `[brands.clickcure] connected_account_id = "acct_xxx"`. (Or wait
   until KYC is complete in §3 — until then the connected account
   can't take live charges anyway; this is just for plumbing tests.)

> 🚦 If you only want to scaffold and test in **test mode** first,
> use the Connect → Test mode toggle, create the connected account
> there, and paste its test-mode `acct_test_xxx` id. The runbook
> works the same in both modes.

---

## 3. Complete KYC for the ClickCure connected account

1. Open the onboarding link Stripe emailed to the connected account
   (or sign in to the connected account directly).
2. Fill in business details:
   - **Business type**: Sole trader / Limited company (whichever is
     accurate for ClickCure's legal entity).
   - **Business name**: `ClickCure`.
   - **Trading address**: registered address.
   - **Website**: `https://clickcure.co`.
   - **Product description**: "Custom UK dental practice landing
     pages, one-time £300 fee."
3. Identity verification:
   - Upload passport or driving licence.
   - Stripe may take up to 3 business days to verify.
4. Add a bank account for **ClickCure** payouts (different from
   Concerto's).
5. Submit.

> Stripe will email when verification is complete. The connected
> account status moves from `restricted` → `enabled`. Until it's
> `enabled`, charges may succeed but payouts are blocked — do not
> announce the new flow publicly until enabled.

---

## 4. Set the ClickCure statement_descriptor + create the £300 price

1. Sign in to the connected account dashboard (top-right account
   switcher in the platform dashboard).
2. **Settings → Public details → Statement descriptor**: set to
   `CLICKCURE.CO`. Save.
3. **Settings → Branding**: upload the ClickCure logo + brand colour.
   This is what the hosted Checkout page will display.
4. **Products → + Add product**:
   - Name: `ClickCure Express`.
   - Description: `Custom landing page for UK dental practice,
     delivered in 48h.`
   - **Pricing model**: One-time.
   - **Price**: `£300.00` (`GBP`).
   - Save. Stripe shows the new `price_xxx` id.
5. Copy that `price_xxx` id. Paste it into BOTH
   `/opt/concerto/backend/concerto/brands.toml` AND
   `/opt/clickcure/core/brands.toml` under
   `[brands.clickcure] express_price_id = "price_xxx"`.
6. Commit + push the brand config update on a NEW small branch
   (`claude/stripe-clickcure-go-live`) and merge into both repos.
   This is the step that flips the ClickCure `/checkout` endpoint
   from 503 to live charging.

---

## 5. Wire the webhook endpoint for the connected account

> Out of WS3 scope but documented here so the runbook is complete.

1. **Connect → Webhooks → + Add endpoint**.
2. URL: `https://api.clickcure.co/webhooks/stripe-clickcure` (or
   whichever endpoint the next sprint's slice ships).
3. Listen to events from **Connected accounts** (not "Account").
4. Select events: `checkout.session.completed`,
   `charge.dispute.created`.
5. Copy the signing secret → paste into
   `STRIPE_CLICKCURE_WEBHOOK_SECRET` env on the canary VPS.

---

## 6. Smoke test before announcing

1. Test mode first:
   - Switch the platform dashboard to **Test mode**.
   - Create a separate test-mode connected account, KYC-skipped.
   - Paste its `acct_test_xxx` into both `brands.toml`.
   - Deploy to a staging VPS or run `python -m core.web_server`
     locally with `STRIPE_SECRET_KEY=sk_test_xxx`.
   - Visit `https://clickcure.co/#pricing` (or local equivalent),
     click **Get Started**, complete a test charge with card
     `4242 4242 4242 4242`.
   - Verify in the connected account's dashboard that the charge
     appears with statement_descriptor `CLICKCURE.CO`.
2. Flip to **Live mode**:
   - Replace `acct_test_xxx` with the live `acct_xxx`.
   - Replace `price_test_xxx` with the live `price_xxx`.
   - Replace `STRIPE_SECRET_KEY` (live), `STRIPE_CLICKCURE_WEBHOOK_SECRET`
     (live) in the prod env file.
   - Restart the clickcure systemd unit.

---

## Rollback plan

If something goes wrong AFTER the ClickCure brand goes live, you
have three escalating rollback options:

### Rollback A (safest, 5 min): re-enter 503 mode

1. Edit `/opt/clickcure/core/brands.toml` on the VPS.
2. Set `connected_account_id = ""` for the `clickcure` brand.
3. Restart the clickcure web server.
4. The `/checkout` endpoint immediately returns HTTP 503 with the
   "temporarily unavailable" page. No customer is charged on the
   wrong brand. Outstanding sessions already started complete
   normally on the connected account.

### Rollback B (revert the migration): drop back to the static
Concerto-shared link

1. `git revert` the WS3 merge commits in `clickcure`:
   `git revert <merge-sha>` on a new branch, push, merge.
2. The old `<a href="https://buy.stripe.com/cNidR882…">` link
   returns. Concerto-branded checkout once again charges ClickCure
   customers (the pre-WS3 status quo).
3. This is the "if everything is on fire" option — accepts the
   original brand-confusion bug rather than blocking sales.

### Rollback C (de-platform the connected account): delete the
ClickCure connected account

1. In the Stripe platform dashboard, **Connect → Connected
   accounts → ClickCure → … → Delete**.
2. Outstanding charges and payouts on that account continue to
   settle but no new sessions can be created.
3. Combine with Rollback A or B.

### Rollback NEVER for Concerto

Concerto's behaviour is unchanged by WS3. Do not roll Concerto back
"as a precaution" — there is nothing to roll back. The
`backend/tests/test_stripe_concerto_regression.py` test pins the
call shape; if it ever fails, that is the signal to investigate, not
to revert blindly.

---

## After-merge config checklist

After the operator finishes §1–§5 and merges
`claude/stripe-clickcure-go-live`, both `brands.toml` files should
look like:

```toml
[brands.concerto]
display_name = "Concerto"
domain = "concerto.run"
support_email = "support@concerto.run"
statement_descriptor = "CONCERTO.RUN"
currency = "usd"
connected_account_id = ""          # Concerto stays on platform account

[brands.clickcure]
display_name = "ClickCure"
domain = "clickcure.co"
support_email = "contact@clickcure.co"
statement_descriptor = "CLICKCURE.CO"
currency = "gbp"
connected_account_id = "acct_xxxxxxxxxxxxxxxxxx"   # ← filled in §2
express_price_id     = "price_xxxxxxxxxxxxxxxx"    # ← filled in §4
```

After that:
- ClickCure visitors see "ClickCure" in the hosted Checkout, the
  statement_descriptor on their card statement, and payouts go to
  the ClickCure bank account.
- Concerto is untouched.
- The unit tests still pass (the configured `acct_xxx` only flips
  one assertion in `test_brand_stripe.py::test_shipped_clickcure_*`
  — update or delete it during that go-live PR).
