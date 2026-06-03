# Concerto Email Routing Matrix

## Overview

All outbound email from Concerto goes through **mailroom** (the shared sending-infrastructure service) as the primary path, using:
- `brand = "concerto"`
- `send_kind = "transactional"`
- `inbox = noreply@concerto.run` (warmup pool, managed by mailroom)

The **raw-SMTP fallback** (Migadu STARTTLS:587) is an *audible, bounded exception* for critical transactional sends only. Non-critical sends are NEVER sent via raw SMTP — failure goes to DLQ to preserve the mailroom pool's warm-up reputation.

---

## Routing policy per email class

| Email class | Examples | `critical` param | Mailroom primary | On mailroom failure | Raw SMTP fallback |
|---|---|:---:|:---:|---|:---:|
| **Transactional critical** | Payment receipts, billing alerts, refund confirmations | `True` (default) | ✅ | SMTP fallback — AUDIBLE (ERROR log + cortex claude_inbox `smtp_fallback` event + counter increment) | ✅ allowed |
| **Non-critical (drip/onboarding)** | Day-0 welcome, Day-1 first session, Day-3 pattern, Day-7 check-in | `False` | ✅ | DLQ (`concerto_email_dead_letter`) + exception raised — no bypass | ❌ forbidden |

### Rationale for the split

- **Critical**: A receipt that fails to deliver after a payment is collected is a customer trust issue. The pool outage must not block the purchase flow. The cost is leaving the pool temporarily — acceptable because it's bounded and AUDIBLE.
- **Non-critical**: Sending drip emails via raw SMTP bypasses mailroom's warmup/rotation logic. During the warm-up period (mailroom is currently in `warmup` status for `noreply@concerto.run`), unauthorized direct sends risk burning sender reputation without the pool's pacing. Failure is better than bypass.

---

## Implementation

**File**: `backend/concerto/transactional.py` — `MigaduSMTPClient.send(critical: bool = True)`

**Decision logic**:

```
mailroom.send(brand="concerto", ...)
  ├── status="sent"       → return provider_message_id   (both classes)
  ├── status="suppressed" → return "<suppressed>"         (both classes)
  ├── status="failed"/"blocked":
  │     critical=True  → _alert_mailroom_fallback() → SMTP fallback
  │     critical=False → _write_dlq() → raise SMTPException
  └── MailroomError (unreachable):
        critical=True  → _alert_mailroom_fallback() → SMTP fallback
        critical=False → _write_dlq() → raise SMTPException
```

**CONCERTO_TRANSACTIONAL_STRICT=1**: Disables the raw-SMTP fallback even for critical sends (DLQ + raise). Not currently set in production (the default bounded-fallback is appropriate).

---

## Audible fallback (critical path only)

When a critical send falls back to raw SMTP, three things happen:
1. **ERROR log**: `MAILROOM SMTP FALLBACK — transactional email bypassed mailroom pool: to=… subject=… reason=…`
2. **Counter file**: `/var/lib/concerto/smtp_fallback_count` incremented (Prometheus-scraped or `cat` by ops).
3. **cortex claude_inbox**: event `kind=smtp_fallback` written with `severity=warning`, actor `concerto-transactional`, project `concerto` — surfaces in the operator orchestrator chat.

---

## Configuration

| Env var | Source | Value | Notes |
|---|---|---|---|
| `MAILROOM_URL` | `/etc/empire/env` | `http://127.0.0.1:8079` | Real mailroom port (not the client default 8099) |
| `CONCERTO_TRANSACTIONAL_STRICT` | not set | — | Default: fallback allowed for critical sends |
| `CONCERTO_SMTP_HOST` | `/etc/empire/env` | `smtp.migadu.com` | Fallback SMTP host |
| `CONCERTO_SMTP_PORT` | `/etc/empire/env` | `587` | STARTTLS |

**Important**: `concerto-drip-runner.service` reads from `/etc/concerto/env` (which lacks `MAILROOM_URL`). The client hardcodes the correct default `http://127.0.0.1:8079` so no env var is needed for drip.

---

## Call sites and their class

| Call site | Class | `critical` |
|---|---|---|
| `concerto.server` → payment receipt (Stripe webhook) | Transactional critical | `True` |
| `concerto.server` → billing alert | Transactional critical | `True` |
| `concerto.drip_runner._send()` → all drip schedules | Non-critical | `False` |
| `concerto.drip_runner.send_immediate_drip()` → J0 welcome | Non-critical | `False` |
