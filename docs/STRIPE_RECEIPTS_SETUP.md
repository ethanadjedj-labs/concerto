# Stripe Receipts & Invoices Setup — Operator Action Required

## 1. Upload Concerto Logo

1. Go to [dashboard.stripe.com/settings/branding](https://dashboard.stripe.com/settings/branding)
2. Upload the Concerto logo (square PNG, min 128×128 px, transparent background)
   - Source: `frontend/public/logo.png` or export the SVG nav icon as PNG
3. Set **Brand colour**: `#7c3aed` (violet-600)
4. Click **Save**

The logo appears on receipt/invoice emails, the Stripe-hosted checkout page, and
the customer portal.

## 2. Enable Receipt Emails

1. Go to **Settings → Customer emails**
2. Enable **Successful payments** (one-time receipts — BYOC plan)
3. Enable **Successful invoices** (monthly invoices — Hosted plan)
4. Optional custom message:
   > "Thanks for using Concerto! Questions? Reply to this email or contact support@concerto.run."

## 3. Hosted Plan — Monthly Invoices

Stripe Billing auto-generates a monthly invoice on each subscription renewal.
Each invoice includes:
- Line item: "Concerto Hosted — $39.00 USD"
- VAT line if applicable (Stripe Tax — see `docs/STRIPE_TAX_SETUP.md`)
- Invoice PDF downloadable from customer portal

No code changes needed.

## 4. BYOC Plan — One-Time Receipts

Stripe sends a receipt automatically after each `checkout.session.completed` for
one-time payments. The receipt includes:
- Line item: "Concerto BYOC — $99.00 USD"
- Tax if applicable
- Stripe order/session reference

## 5. EU Invoice Compliance

For EU B2B customers who enter a VAT number at checkout, Stripe automatically:
- Applies reverse-charge (0% VAT)
- Adds "Reverse charge — VAT to be accounted for by the customer"
- Includes the customer's VAT number on the invoice
- Includes **your** VAT number — **required action**: add it in
  **Settings → Business details → Tax ID**

## 6. Enable Customer Portal (Required for Hosted plan)

1. Go to [dashboard.stripe.com/settings/billing/portal](https://dashboard.stripe.com/settings/billing/portal)
2. Enable the portal
3. Set **Return URL**: `https://concerto.run/dashboard`
   (Concerto appends the customer token dynamically)
4. Enable features:
   - ✅ Update payment method
   - ✅ Cancel subscriptions
   - ✅ View billing history / download invoices
5. Click **Save**

## 7. Invoice Number Prefix (Optional)

**Settings → Invoice and Quote** → set prefix (e.g. `MST-`) for invoice numbers
like `MST-0001`. Useful for accounting.

## 8. Currency Localisation — Why USD Only in v1

- Multi-currency requires maintaining separate Price objects per currency and
  handling FX risk/rounding on the recurring billing side.
- For v1 (sub-100 customers), complexity outweighs the conversion benefit.
- EU customers see the USD price + VAT displayed separately by Stripe Tax.
  Their bank applies the FX rate at card charge time.
- **Deferred to v1.5**: Add EUR and GBP presentment via `currency_options` on
  the Stripe Price object once MRR justifies it.

## Operator Action Summary

| Action | Where | Notes |
|--------|-------|-------|
| Upload logo | Stripe → Settings → Branding | PNG 128px+, transparent |
| Set brand colour #7c3aed | Stripe → Settings → Branding | Violet |
| Enable receipt emails | Stripe → Settings → Customer emails | Both plans |
| Add business VAT number | Stripe → Settings → Business details → Tax ID | EU compliance |
| Enable customer portal | Stripe → Settings → Billing → Customer portal | Hosted plan |
| Set return URL for portal | Same as above | https://concerto.run/dashboard |
| Set invoice number prefix | Stripe → Settings → Invoice and Quote | Optional |
