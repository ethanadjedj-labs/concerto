# Stripe Tax Setup — Operator Action Required

Concerto's checkout already passes `automatic_tax: { enabled: true }` to Stripe Checkout.
Before going live you must activate Stripe Tax in the dashboard.

## 1. Enable Stripe Tax

1. Log into [dashboard.stripe.com](https://dashboard.stripe.com)
2. Go to **Tax** in the left sidebar
3. Click **Get started** → follow the activation wizard
4. Enter your business address (determines nexus and applicable rates)

## 2. Add Tax Registrations

Stripe Tax only collects tax in jurisdictions where you have an active registration.

### United States (Sales Tax)

1. In **Tax → Registrations**, click **Add registration** → **United States**
2. Select states where you have economic nexus (start with your home state)
3. Stripe calculates the applicable sales-tax rate per customer billing address

### European Union (VAT via One Stop Shop — OSS)

1. Once EU revenue exceeds €10,000/yr (or immediately if preferred), register for
   the EU OSS scheme in your country of establishment
2. In **Tax → Registrations** → **European Union** → enter your OSS VAT number
3. Stripe collects the correct VAT rate for each EU member state automatically

### United Kingdom (VAT)

Register with HMRC when UK revenue exceeds £85,000/yr, then add to Stripe:
**Tax → Registrations** → **United Kingdom** → enter UK VAT number.

## 3. B2B Reverse Charge (EU)

Stripe Checkout automatically displays a VAT number field for EU customers.
A valid VAT number triggers the reverse-charge rule (0% VAT, note on invoice:
"Reverse charge — VAT to be accounted for by the customer"). No code changes needed.

## 4. What the Code Does

- `frontend/app/api/checkout/route.ts` passes `automatic_tax: { enabled: true }`
  to `stripe.checkout.sessions.create()`
- Stripe detects customer location via billing address and card country
- Tax is itemised on Stripe-generated receipts and invoices automatically
- No application-level tax calculation is required

## 5. Currency Note

Concerto prices in USD. EU customers see USD price + VAT shown separately by Stripe.
Multi-currency presentment is deferred to v1.5 — see `docs/STRIPE_RECEIPTS_SETUP.md`.

## Operator Action Summary

| Action | Where | Priority |
|--------|-------|----------|
| Enable Stripe Tax | Dashboard → Tax | Required before launch |
| Add US state registrations | Tax → Registrations → US | Required if US sales |
| Register EU OSS + add to Stripe | Tax → Registrations → EU | Required if EU sales |
| Register UK VAT (if applicable) | HMRC + Stripe → Tax | When revenue > £85k |
