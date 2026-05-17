# Privacy Policy

**Concerto** — Remote Workshop for Claude Code Agents

_Last updated: 2026-05-17_

---

## 1. Who We Are

Concerto is operated by Ethan Adjedj. You can reach us at **privacy@concerto.run**. For GDPR purposes, we are the data controller for the limited personal data described below.

---

## 2. What We Collect — and What We Don't

### What we DO collect

| Data | Why | How long |
|------|-----|----------|
| **Buyer email address** | Received from Stripe after a successful purchase. Used to send your onboarding email and dashboard link. | 30 days after purchase, then anonymised |
| **DigitalOcean API key** | Entered by you during onboarding. Used once to provision your Droplet, then **permanently deleted** from our database. We never store it beyond the time needed to make the DO API call. | Deleted immediately after provisioning completes |
| **Dashboard token** (UUID) | Generated at purchase. Acts as your authentication credential for the dashboard. | Retained while your session is active; anonymised 30 days post-purchase |
| **Droplet metadata** | Droplet ID, IP address, and provisioning status — necessary to route your terminal session and show dashboard status. | Retained for 30 days post-purchase, then anonymised |

### What we explicitly do NOT collect

- The code you write or run on your Droplet
- Your Claude Code conversations or agent outputs
- Keystrokes entered in the embedded terminal
- Browser fingerprints, behavioural analytics, or ad-targeting data
- Any data from your DigitalOcean account beyond what is needed to create a single Droplet

---

## 3. Where Your Data Lives

Our backend runs on a VPS in **Hetzner's Falkenstein datacenter** (Germany, EU). Data is stored in a SQLite database on that server. Hetzner is certified to ISO/IEC 27001 and operates within the EU under GDPR jurisdiction.

No personal data is transferred to jurisdictions outside the EU/EEA in the course of normal service operation, with the exception of the processors listed in Section 6.

---

## 4. Cookies and Tracking

Concerto does not use cookies for tracking or analytics. We do not embed tracking pixels, use ad networks, or run third-party analytics scripts.

Stripe Checkout sets its own cookies during the payment flow. These are governed by [Stripe's Privacy Policy](https://stripe.com/privacy) and are outside our control.

Your dashboard session is authenticated via a URL-embedded UUID token, not cookies.

---

## 5. Lawful Basis for Processing (GDPR)

| Processing activity | Lawful basis |
|--------------------|-------------|
| Sending onboarding email | **Contract performance** (Art. 6(1)(b)) — necessary to deliver the purchased service |
| Storing Droplet metadata | **Contract performance** — necessary to operate your dashboard |
| DigitalOcean API key (transient) | **Contract performance** — you provided it expressly for this purpose |
| Retaining anonymised analytics | **Legitimate interest** (Art. 6(1)(f)) — improving service reliability |

---

## 6. Data Processors

We share data with the following third parties to deliver the service:

| Processor | Purpose | Data shared | Privacy info |
|-----------|---------|-------------|-------------|
| **Stripe, Inc.** | Payment processing | Email address, payment card (card data goes directly to Stripe — we never see it) | stripe.com/privacy |
| **Resend** | Transactional email delivery | Email address | resend.com/legal/privacy-policy |
| **DigitalOcean, LLC** | Droplet provisioning — **customer-controlled** | Your DO API key (used transiently), Droplet creation request | digitalocean.com/legal/privacy-policy |
| **Hetzner Online GmbH** | VPS hosting for our backend | All data stored in our database (encrypted at rest) | hetzner.com/legal/privacy-policy |

We do not sell or rent your data to any party.

---

## 7. Your Rights Under GDPR

If you are located in the EU/EEA, you have the following rights:

- **Right of access** — request a copy of the data we hold about you
- **Right to rectification** — correct inaccurate data
- **Right to erasure** ("right to be forgotten") — request deletion of your data at any time by emailing **privacy@concerto.run**. We will process deletion requests within 30 days.
- **Right to restrict processing** — ask us to pause processing while a dispute is resolved
- **Right to data portability** — receive your data in a machine-readable format
- **Right to object** — object to processing based on legitimate interest
- **Right to lodge a complaint** — with your national supervisory authority (e.g., CNIL in France, ICO in the UK)

To exercise any of these rights, email **privacy@concerto.run** with your purchase email address. We do not charge for these requests and will respond within 30 days.

---

## 8. Data Retention

- Personal data (email, token, Droplet metadata) is retained for **30 days** after your purchase date.
- After 30 days, records are anonymised: email is hashed, IP addresses are zeroed, tokens are replaced with opaque identifiers.
- Anonymised aggregate data (e.g., provisioning success rates) may be retained indefinitely for operational analytics.
- Your DigitalOcean API key is **never retained** past the provisioning step.

---

## 9. Security

- All API traffic is encrypted in transit via TLS/HTTPS.
- The backend database is stored on encrypted Hetzner block storage.
- Your DO API key is held in memory only for the duration of the DO API call, then discarded.
- Dashboard tokens are cryptographically random 128-bit UUIDs; they cannot be guessed.

---

## 10. Changes to This Policy

We will post any material changes here with an updated "Last updated" date and, where required, notify you by email.

---

## 11. Contact

**Email**: privacy@concerto.run

We respond to privacy requests within 30 days.
