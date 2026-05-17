# Concerto Operator Support Setup Runbook

This document covers everything you need to stand up support infrastructure for Concerto: email support routing and auto-responder templates.

---

## 1. Support channel

Concerto support is **email only**: support@concerto.run via Migadu.
Email only — no community forums. Every reply is from a real human within 24 hours.

## 2. Support Email — support@concerto.run

### 2.1 DNS prerequisite

`concerto.run` must be acquired and delegated to Cloudflare before email can be configured. See [pending operator action #1 in MANAGER_STATE.md].

### 2.2 Option A — Migadu (recommended)

**Cost**: $19/yr (Micro plan) — unlimited mailboxes and aliases, inbound routing included.

**Pros**:
- Cheapest inbound option for unlimited addresses
- Full IMAP/SMTP access (useful if you want to read support tickets programmatically)
- No per-message pricing
- Good DKIM/SPF tooling

**Cons**:
- Requires manual DNS record setup (MX, SPF, DKIM, DMARC)
- Web UI is functional but dated

**Setup steps**:
1. Sign up at https://www.migadu.com → select **Micro** plan.
2. Add domain `concerto.run`. Migadu will show you MX, SPF, DKIM, DMARC records.
3. In Cloudflare (zone `d4f729f470a0804a4ef89ff0dc8281ad`), add:
   - `MX concerto.run → aspmx1.migadu.com` (priority 10)
   - `MX concerto.run → aspmx2.migadu.com` (priority 20)
   - `TXT concerto.run → "v=spf1 include:spf.migadu.com ~all"`
   - `TXT _dmarc.concerto.run → "v=DMARC1; p=quarantine; rua=mailto:dmarc@concerto.run"`
   - `CNAME key1._domainkey.concerto.run → key1.concerto.run._domainkey.migadu.com`
4. Create mailbox: `support@concerto.run` (forward to `adjedjethan@gmail.com` or team inbox).
5. Create alias: `noreply@concerto.run` → discard (for transactional email From address).

### 2.3 Option B — Resend Inbound (alternative)

**Cost**: Free tier (100 inbound/day); $20/mo for higher volume.

**Pros**:
- Already integrated with transactional outbound (Resend API key in `/etc/cortex/env`)
- Webhook-based inbound — easy to wire into a ticket system
- Same dashboard for inbound + outbound

**Cons**:
- No native IMAP — replies must be sent via Resend API or a separate SMTP provider
- Inbound webhooks require a public endpoint to receive tickets
- More expensive at volume vs Migadu

**Setup**: Resend dashboard → Domains → `concerto.run` → Inbound → enable. Point MX to Resend's servers. Configure webhook URL: `https://api.concerto.run/webhooks/inbound-email`.

### 2.4 Recommendation

**Use Migadu**. At $19/yr it costs less than one month of Resend paid. Inbound email for a support channel does not need real-time webhooks at launch — a daily email review is sufficient. Migrate to Resend Inbound later if you want ticket automation.

---

## 3. Auto-Responder Templates

When a support email arrives at `support@concerto.run`, an auto-responder should acknowledge receipt immediately.

### 3.1 English template

**Subject**: `Re: {{original_subject}} — We received your message`

```
Hi,

Thanks for reaching out to Concerto support. We've received your message and will get back to you within 24 hours (usually sooner).

While you wait, you might find an answer in our:
• Help center: https://concerto.run/help
• Email: support@concerto.run (human reply within 24 hours)

— The Concerto team
support@concerto.run | https://concerto.run
```

### 3.2 French template

**Subject**: `Re: {{original_subject}} — Votre message a bien été reçu`

```
Bonjour,

Merci de nous avoir contacté. Votre message a bien été reçu et nous vous répondrons dans les 24 heures (souvent plus tôt).

En attendant, vous trouverez peut-être une réponse dans :
• Notre centre d'aide : https://concerto.run/help
• Email : support@concerto.run (réponse humaine sous 24 heures)

— L'équipe Concerto
support@concerto.run | https://concerto.run
```

### 3.3 Implementation

Migadu supports auto-responders natively under mailbox settings → **Vacation / Auto-Reply**. Paste the EN template there. For bilingual detection (based on sender IP or email language headers), a lightweight Cloudflare Worker could route and reply — skip this until volume justifies it.

---

## 4. MANAGER_STATE Pending Actions

Add these to the pending operator actions list:

- [ ] **Acquire concerto.run** and delegate NS to Cloudflare (prerequisite for all email setup)
- [ ] **Migadu**: sign up, add domain, add DNS records in Cloudflare, create `support@concerto.run` mailbox
- [ ] **Email**: set up support@concerto.run Migadu mailbox (see section 2)
- [ ] **Carl-bot**: invite, configure autorole + welcome message
- [ ] **Stripe webhook**: verify checkout.session.completed sends confirmation email
- [ ] **status.concerto.run DNS**: add CNAME → Vercel (once status page is deployed)
