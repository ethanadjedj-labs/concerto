# Email Infrastructure — Concerto

## Overview

Concerto uses **Migadu SMTP** (smtp.migadu.com:587, STARTTLS) for all outbound email from the `concerto.run` domain. The implementation is a stdlib-only Python SMTP client (`backend/concerto/transactional.py`) with no external dependencies.

**Resend** (`RESEND_API_KEY`) remains in the environment for `strandedgrid.com` outbound only. Do not use it for concerto.run email.

---

## Rationale

| Option | Cost | Sending limit | Notes |
|---|---|---|---|
| Resend Free | $0 | 100/day, 1 domain | `strandedgrid.com` already occupies the free domain slot |
| Resend Pro | $20/mo | 50K/mo | Unnecessary — Migadu already paid |
| **Migadu** | **$0 incremental** | **200/day (scales)** | $19/yr already paid for the account |

Migadu was chosen because the account was already purchased ($19/yr, unlimited mailboxes), the `concerto.run` domain was added at no extra cost, and Hetzner allows port 587 outbound (STARTTLS) even though port 465 is blocked.

---

## Mailboxes

| Mailbox | Purpose |
|---|---|
| `noreply@concerto.run` | All outbound transactional mail (From:). Password in `/etc/cortex/env` as `CONCERTO_SMTP_PASS_NOREPLY` |
| `support@concerto.run` | Reply-To: on all emails. Full mailbox, forwarded to `adjedjethan@gmail.com`. Password in `/etc/cortex/env` as `CONCERTO_SMTP_PASS_SUPPORT` |

---

## DNS Records

All records live in Cloudflare (zone `208681448c90a193489a0907a48f6166`).

| Type | Name | Value |
|---|---|---|
| MX | `concerto.run` | `aspmx1.migadu.com` (priority 10), `aspmx2.migadu.com` (priority 20) |
| TXT | `concerto.run` | `v=spf1 include:spf.migadu.com -all` |
| CNAME | `key1._domainkey.concerto.run` | `key1.concerto.run._domainkey.migadu.com` |
| CNAME | `key2._domainkey.concerto.run` | `key2.concerto.run._domainkey.migadu.com` |
| CNAME | `key3._domainkey.concerto.run` | `key3.concerto.run._domainkey.migadu.com` |
| TXT | `_dmarc.concerto.run` | `v=DMARC1; p=quarantine; rua=mailto:dmarc@concerto.run` |

---

## Env Vars (in `/etc/cortex/env`)

```
CONCERTO_SMTP_HOST=smtp.migadu.com
CONCERTO_SMTP_PORT=587
CONCERTO_SMTP_USER_NOREPLY=noreply@concerto.run
CONCERTO_SMTP_PASS_NOREPLY=<32 hex>
CONCERTO_SMTP_USER_SUPPORT=support@concerto.run
CONCERTO_SMTP_PASS_SUPPORT=<32 hex>
CONCERTO_EMAIL_FROM=noreply@concerto.run
CONCERTO_EMAIL_REPLY_TO=support@concerto.run
```

---

## Architecture

```
send_email() / send_operator_alert()   ← stripe_webhook, refunds, monitoring, trial_router
        │
        ▼
email_utils.py  (async wrapper)
        │
        ▼
transactional.MigaduSMTPClient.send_async()
        │  (asyncio.to_thread)
        ▼
transactional.MigaduSMTPClient.send()   ← drip_runner, trial_reaper (sync)
        │
        ├─ smtplib.SMTP (STARTTLS:587)
        │    retry 3× (1s / 2s / 4s backoff)
        │
        └─ on failure → concerto_email_dead_letter (SQLite)
```

### Dead-Letter Queue

Emails that exhaust all 3 retries are written to `concerto_email_dead_letter` in the concerto SQLite DB (`/var/lib/concerto/concerto.db`).

```sql
SELECT * FROM concerto_email_dead_letter ORDER BY attempted_at DESC LIMIT 20;
```

Fields: `to_addr`, `subject`, `body_html`, `body_text`, `error`, `attempted_at`, `retries`.

To re-send a dead-lettered email manually, use `ops/scripts/test_email_send.py` to verify SMTP is healthy, then resend via the backend API or shell.

---

## Daily Send Cap

Migadu paid plan: **200 emails/day** on the standard tier. Concerto's drip sequence fires at most 1–2 emails/day per active subscriber. At 200 daily active subscribers the cap would be reached — upgrade Migadu to a higher tier (contact Migadu support) or switch to a dedicated IP plan when approaching scale.

---

## Troubleshooting

### Verify SMTP is working

```bash
source /etc/cortex/env
python ops/scripts/test_email_send.py
```

Exit 0 = sent. Exit 1 = SMTP error (see message). Exit 2 = env vars missing.

### Check Migadu domain state via API

```bash
source /etc/cortex/env
curl -u "$MIGADU_API_USER:$MIGADU_API_KEY" \
  https://api.migadu.com/v1/domains/concerto.run | python3 -m json.tool
```

Key field: `state`. If `"inactive"`, DNS hasn't propagated or Migadu hasn't validated yet — wait 5–60 minutes and check again.

### Domain shows "inactive" after DNS propagation

1. Verify DNS is correct: `dig TXT concerto.run | grep spf` — should show `v=spf1 include:spf.migadu.com -all`
2. Verify DKIM CNAMEs: `dig CNAME key1._domainkey.concerto.run` — should resolve to `key1.concerto.run._domainkey.migadu.com`
3. Log into Migadu admin (`app.migadu.com`) → Domains → concerto.run → Run DNS check
4. Migadu auto-activates within 5 min–1 h after all records resolve

### Emails not arriving (check spam)

- Reply-To is `support@concerto.run` — instruct users to add to contacts
- Check DMARC: `dig TXT _dmarc.concerto.run` — should show `p=quarantine`
- Check dead-letter queue: `sqlite3 /var/lib/concerto/concerto.db "SELECT to_addr, subject, error FROM concerto_email_dead_letter ORDER BY attempted_at DESC LIMIT 10;"`

### Port 465 blocked (Hetzner)

Hetzner VPS blocks port 465 outbound. The client uses port **587** (STARTTLS), which works. Do not change to 465.
