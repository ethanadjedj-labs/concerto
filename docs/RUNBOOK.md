# Concerto Operator Runbook — 48h Post-Launch Playbook

> **Audience**: Ethan only. Every command is copy-paste ready. Every decision tree ends in a concrete action.
> **Last updated**: 2026-05-17
> **Related docs**: `MANAGER_STATE.md` (strategic state), `SUPPORT_SETUP.md` (Discord/email infra), `CUSTOM_STYLE.md` (operator kit)

---

## 1. Day 0 Launch Checklist

Run this top-to-bottom ≤1h before posting publicly. Check each box before moving to the next.

### DNS

```bash
dig concerto.run NS
# Expected: jonah.ns.cloudflare.com + kiki.ns.cloudflare.com
curl -I https://concerto.run
# Expected: HTTP/2 200
curl -I https://api.concerto.run/healthz
# Expected: {"status":"ok","service":"concerto-backend"}
```

Cloudflare zone: `208681448c90a193489a0907a48f6166`. If NS doesn't resolve to Cloudflare, log into NameSilo and verify nameserver delegation.

### Stripe

- [ ] Webhook endpoint registered: `https://api.concerto.run/webhooks/stripe-concerto`
- [ ] Webhook signing secret in `/etc/cortex/env` as `STRIPE_WEBHOOK_SECRET`
- [ ] Fire a test event:

```bash
stripe trigger checkout.session.completed
# Then check: journalctl -u concerto-backend -n 30 | grep -i "stripe\|webhook"
# Expected: log line showing event received + buyer row created
```

- [ ] `STRIPE_CONCERTO_PRICE_ID` set (one-time BYOC)
- [ ] `STRIPE_CONCERTO_HOSTED_PRICE_ID` set (monthly hosted)
- [ ] Stripe Tax enabled in Dashboard → Tax → Enable automatic tax
- [ ] Stripe test mode OFF (live mode active) before posting

### DigitalOcean

```bash
DO_TOKEN=$(grep CONCERTO_DO_API_TOKEN /etc/cortex/env | cut -d= -f2)
curl -s -H "Authorization: Bearer $DO_TOKEN" https://api.digitalocean.com/v2/account \
  | python3 -m json.tool | grep -E "email|droplet_limit|status"
# Expected: status: active, email matches Ethan's DO account
```

- [ ] DO account funded ≥$100 (check billing page, add payment method as backup)
- [ ] Droplet limit ≥20 (request increase if at default 10)

### Systemd services

```bash
systemctl is-active \
  concerto-backend \
  concerto-hosted-lifecycle.timer \
  concerto-drip-runner.timer \
  concerto-status-writer.timer \
  concerto-monitoring.timer
# All 5 must print "active"
```

If any is inactive:
```bash
systemctl status <unit> --no-pager -l
journalctl -u <unit> -n 30
systemctl restart <unit>
```

### End-to-end test (Stripe test mode)

1. Switch Stripe to **test mode**
2. Create a test checkout session via the Concerto purchase URL
3. Pay with card `4242 4242 4242 4242`, any future date, any CVC
4. Confirm in Stripe Dashboard → Events → `checkout.session.completed`
5. Check empire backend logs for buyer row creation:
   ```bash
   journalctl -u concerto-backend -n 50 | grep -E "buyer|provision|droplet"
   ```
6. For Hosted: verify droplet appears in DO Console within 3 min
7. Open `/dashboard/<token>` — stepper should advance through Provisioning → OAuth
8. Make a first MCP tool call from the customer droplet
9. Confirm `first_call_at` populated:
   ```bash
   sqlite3 /var/lib/concerto/concerto.db \
     "SELECT email, status, first_call_at FROM concerto_buyers ORDER BY created_at DESC LIMIT 3;"
   ```
10. Switch Stripe back to **live mode**

### Communications infrastructure

- [ ] Discord server live at permanent invite link — test join from incognito
- [ ] `NEXT_PUBLIC_DISCORD_INVITE_URL` set in Vercel env vars
- [ ] Send email to `support@concerto.run`, verify receipt in mailbox (Migadu)
- [ ] Status page green: visit `https://status.concerto.run` — all indicators green

### Email templates

Preview each template by opening the HTML file in a browser (not an email client):

```bash
ls /opt/concerto/emails/drip/
# day_0.html  day_1.html  day_3.html  day_7.html  day_14.html  day_21.html  day_30.html
```

Check: correct brand name (Concerto, not Maestro), working links, no broken images.

---

## 2. First Customer Arrives — Minute-by-Minute Playbook

> Clock starts when Stripe fires `checkout.session.completed`.

### 0:00 — Stripe webhook fires

- Open Stripe Dashboard → Developers → Webhooks → your endpoint
- Confirm the event shows `200 OK` delivery
- If `503` or no delivery: check `journalctl -u concerto-backend -n 20` for crash; restart if needed

### 0:02 — Confirm buyer row created

```bash
journalctl -u concerto-backend -n 50 | grep -E "buyer|created|provision"
```

Expected: log line like `buyer created: email=<x> token=<y> plan=hosted|byoc`.

Also verify directly in DB:

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT email, plan, status, created_at FROM concerto_buyers ORDER BY created_at DESC LIMIT 1;"
```

### 0:05 — Hosted plan: verify droplet provisioning

- Open DO Console → Droplets → confirm a new droplet is in "creating" state
- Name pattern: `concerto-<token-prefix>`
- If no droplet after 5 min: check `journalctl -u concerto-hosted-lifecycle -n 30`

### 0:15 — If droplet still "creating"

```bash
# SSH into empire, check cloud-init scraper
journalctl -u concerto-hosted-lifecycle -n 50
# Look for: "waiting for cloud-init", "status: running", "error"
```

DO droplets take 30–90s to boot; cloud-init can take 3–8 min depending on package installs. Only escalate if still "creating" at 15 min.

### 0:30 — Customer /dashboard should show ready state

Open `https://concerto.run/dashboard/<token>`.

- Step 1 (Provisioning): green checkmark
- Step 2 (OAuth Claude): either pending (normal) or green if customer already logged in
- Step 3 (Install Connector): copy fields visible

If step 1 is still spinning:

```bash
# Check OAuth status endpoint
curl http://127.0.0.1:8090/api/buyer/<token>/oauth-status
# Check ttyd terminal
curl -s https://api.concerto.run/api/buyer/<token>/oauth-status | python3 -m json.tool
```

### 0:45 — First MCP call expected

```bash
journalctl -u concerto-backend -n 50 | grep -i "first_call\|mcp\|tool"
```

If customer hasn't made a call: they may still be setting up connector. No action needed yet.

Check `first_call_at` column:

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT email, first_call_at FROM concerto_buyers ORDER BY created_at DESC LIMIT 1;"
```

### 1:00 — Welcome nudge

If customer hasn't joined Discord: send a manual welcome DM via the email they used at purchase. See template "Welcome, you're in!" in section 8.

---

## 3. Common Failure Scenarios

### 3.1 DO API Key Rejected (BYOC customer)

**Symptom**: Customer submits their DO API key; backend returns error or provisioning never starts.

**Diagnose**:
```bash
journalctl -u concerto-backend -n 30 | grep -i "do_api\|digitalocean\|invalid\|token"
```

**Remediate**:
1. Check the error message — most likely `401 Unauthorized` or `403 Forbidden`
2. Ask customer to regenerate their DO token with **write** scope (not read-only)
3. If already charged and provisioning failed: issue Stripe refund manually:
   - Stripe Dashboard → Payments → find payment → Refund
4. Email customer (see template "We've issued your refund" in section 8)
5. Mark buyer row:
   ```bash
   sqlite3 /var/lib/concerto/concerto.db \
     "UPDATE concerto_buyers SET status='refunded', refunded_at=datetime('now') WHERE email='CUSTOMER@EMAIL';"
   ```

### 3.2 Droplet Boot Fails

**Symptom**: DO shows droplet in error state or it never reaches "active".

**Diagnose**:
1. DO Console → Droplets → click droplet → "Console" tab (VNC)
2. Look for kernel panic, disk errors, or network errors
3. Check DO status page: `https://status.digitalocean.com`

**Decision**:
- **DO infrastructure issue** (their status page shows incident): wait, email customer, auto-refund after 30 min
- **cloud-init script error**: SSH to droplet if accessible, see 3.3
- **Unknown**: destroy the droplet, issue refund, investigate before retry

**Destroy + refund**:
```bash
# Get droplet ID
DROPLET_ID=$(sqlite3 /var/lib/concerto/concerto.db \
  "SELECT do_droplet_id FROM concerto_buyers WHERE email='CUSTOMER@EMAIL';")
# Destroy
curl -s -X DELETE \
  -H "Authorization: Bearer $(grep CONCERTO_DO_API_TOKEN /etc/cortex/env | cut -d= -f2)" \
  "https://api.digitalocean.com/v2/droplets/$DROPLET_ID"
```

Then issue Stripe refund manually and email customer (see section 8 template "Your droplet failed to provision").

### 3.3 cloud-init Hangs

**Symptom**: Droplet is "active" in DO but customer dashboard stays on step 1 for >10 min.

**Diagnose**:
```bash
DROPLET_IP=<from-DO-console>
ssh root@$DROPLET_IP 'tail -50 /var/log/cloud-init-output.log'
```

**Common causes**:
- `apt-get` stalled waiting for lock: `ssh root@$DROPLET_IP 'ps aux | grep apt'`
- Package install failed: look for `E: Unable to fetch` or `dpkg: error`
- Network timeout fetching packages: retry after 5 min

**Remediate**:
```bash
# If apt is locked, kill it and retry
ssh root@$DROPLET_IP 'kill $(pgrep apt) 2>/dev/null; apt-get install -f -y'
# If cloud-init itself is stuck
ssh root@$DROPLET_IP 'cloud-init status --wait'
```

If cloud-init cannot be recovered within 30 min, treat as droplet boot failure (see 3.2): destroy, refund, investigate.

### 3.4 Cloudflared Tunnel Never Captures URL

**Symptom**: Customer droplet is running but `oauth-status` endpoint returns no tunnel URL; dashboard step 2 never resolves.

**Diagnose**:
```bash
ssh root@$DROPLET_IP 'journalctl -u cloudflared -n 30'
# or
ssh root@$DROPLET_IP 'systemctl status cloudflared'
```

**Remediate — manual tunnel assignment**:
```bash
# On the droplet
ssh root@$DROPLET_IP
cloudflared tunnel create concerto-<token>
cloudflared tunnel route dns concerto-<token> <token>.concerto.run
# Get the tunnel credentials file path from output
systemctl restart cloudflared
```

Then update the buyer row with the assigned URL:
```bash
sqlite3 /var/lib/concerto/concerto.db \
  "UPDATE concerto_buyers SET tunnel_url='https://<token>.concerto.run' WHERE email='CUSTOMER@EMAIL';"
```

Notify customer via email that their instance URL is `https://<token>.concerto.run`.

### 3.5 Customer OAuth Claude Fails

**Symptom**: Customer sees OAuth error on dashboard step 2; `oauth-status` endpoint returns `logged_in: false` after they've tried.

**Most likely cause**: Customer does not have an **Anthropic Max plan**. Claude's OAuth flow requires Max subscription.

**Email** (see template "Here's how to reset your Claude OAuth" in section 8):
- Confirm they're using a Max plan account at claude.ai
- Have them try incognito browser + re-authorize
- If they don't have Max: Concerto requires it; issue full refund

**Check**:
```bash
curl http://127.0.0.1:8090/api/buyer/<token>/oauth-status
# If {"logged_in": false} persists after 3 attempts, it's not a transient error
```

### 3.6 Customer Can't Paste Connector in claude.ai

**Symptom**: Customer has the MCP connector fields from dashboard step 3 but can't get them to work in claude.ai.

**This is a UX friction issue, not a backend failure.**

**Remediate**:
1. Invite customer to Discord — offer a 10 min screenshare
2. Walk through: claude.ai → Settings → Integrations → Add MCP Server → paste URL + token
3. Common mistakes: trailing space in token, wrong URL field, missing `https://`
4. If claude.ai UI has changed, consult latest claude.ai documentation

### 3.7 Stripe Payment Fails After 7 Days (Hosted)

**Symptom**: Customer's monthly payment fails on renewal; Stripe sends dunning emails but subscription lapses.

**How grace period works**: Stripe retries failed payments up to 3 times over 7 days (configurable in Stripe Dashboard → Settings → Subscriptions → Retry schedule). During this window, service continues.

**Diagnose**:
```bash
stripe events list --limit 10 | grep -i "payment_failed\|invoice"
```

**Remediate**:
- If customer updates payment method before grace period ends: automatic retry succeeds, no action
- If grace period exhausted: Stripe cancels subscription; concerto-hosted-lifecycle detects cancellation
- Manual pause (give customer more time):
  ```bash
  # Stripe CLI: pause subscription
  stripe subscriptions update <sub_id> --pause-collection-behavior=mark_uncollectible
  ```
- Manual resume after customer updates card:
  ```bash
  stripe subscriptions update <sub_id> --pause-collection-behavior=void
  ```
- If customer churns: destroy droplet to recover DO costs:
  ```bash
  # See destroy command in 3.2 above
  ```

### 3.8 Customer Requests Refund Outside Policy

**Policy**: Full refund within 72h of purchase if provisioning failed. No refund after first MCP call confirmed (service was used). Partial refund at operator discretion for partial service.

**Decision tree**:

```
Was provisioning successful?
  NO → Full refund, no questions
  YES → Was first_call_at populated?
    NO → Day count?
      < 3 days → Full refund (good faith)
      3–7 days → 50% refund or escalate
      > 7 days → Decline, offer Discord support
    YES → Service was used → Decline
       → Exception: documented technical failure → Full refund
```

**Issue refund**:
1. Stripe Dashboard → Payments → find payment → Refund
2. Update DB:
   ```bash
   sqlite3 /var/lib/concerto/concerto.db \
     "UPDATE concerto_buyers SET status='refunded', refunded_at=datetime('now') WHERE email='CUSTOMER@EMAIL';"
   ```
3. Email customer (see template "We've issued your refund" in section 8)

### 3.9 Empire VPS Goes Down

**Symptom**: `curl http://127.0.0.1:8090/healthz` times out; all customer droplets still running (they're separate DO droplets), but API and dashboard are unreachable.

**Emergency contacts**:
- Hetzner Console: `https://console.hetzner.cloud` — log in with Hetzner account
- Hetzner support ticket: open via console → Support
- Cloudflare status: `https://www.cloudflarestatus.com`

**Recovery steps**:
1. Log into Hetzner Console → check server status
2. If server is "off": Start it from console
3. If server is unresponsive: Power cycle via console
4. After reboot, verify services auto-started:
   ```bash
   systemctl is-active concerto-backend concerto-hosted-lifecycle.timer concerto-drip-runner.timer concerto-status-writer.timer concerto-monitoring.timer
   ```
5. If any failed to start after reboot:
   ```bash
   systemctl reset-failed <unit>
   systemctl start <unit>
   ```

**What data is lost vs persistent**:
- `/var/lib/concerto/concerto.db` — **persistent** (on Hetzner volume or local disk — verify with `df -h`)
- Customer droplets — **not affected** (they're DO droplets, completely separate)
- In-flight provisioning requests — **lost** (check `status='provisioning'` rows and manually retry)
- Cloudflared tunnel — **auto-reconnects** on service restart

**Verify data integrity after recovery**:
```bash
sqlite3 /var/lib/concerto/concerto.db "PRAGMA integrity_check;"
# Expected: ok
```

---

## 4. Daily Operations (15 min/day)

Run each morning:

### 4.1 Check for stuck or failed buyers

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT email, plan, status, created_at FROM concerto_buyers \
   WHERE status IN ('failed_install','provisioning','pending') \
   ORDER BY created_at DESC;"
```

Any row stuck in `provisioning` for >30 min needs manual investigation (see section 3.2/3.3).

### 4.2 Check Stripe for failed payments

- Stripe Dashboard → Payments → filter by "Failed"
- Also check: Radar → Reviews for any flagged payments

### 4.3 Check Discord

Open Discord server → scan `#support` and `#general` for unanswered messages. SLA target: reply within 4h during waking hours.

### 4.4 Check status page

Visit `https://status.concerto.run`. If any indicator is red:
- Check the corresponding service: `journalctl -u concerto-backend -n 30`
- Check DO API reachability: `curl -s -o /dev/null -w "%{http_code}" https://api.digitalocean.com/v2`
- Check Stripe: `curl -s -o /dev/null -w "%{http_code}" https://api.stripe.com/v1`

### 4.5 Quick log scan

```bash
journalctl -u concerto-backend --since "24h ago" | grep -iE "error|exception|traceback|5[0-9]{2}" | tail -30
```

---

## 5. Weekly Operations (1h/week)

### 5.1 Stripe revenue summary

- Stripe Dashboard → Reports → Revenue
- Note: MRR (hosted), one-time BYOC revenue, refund rate
- Target refund rate: <5%

### 5.2 DO billing review

- DO Console → Billing → current month
- Cross-reference: hosted customers × $6–12/mo DO cost vs $39/mo revenue
- Gross margin target: >60% per hosted customer

### 5.3 Anthropic API usage

- If any API calls are running on Ethan's account (not customer accounts): review at console.anthropic.com
- Concerto customers use their own Anthropic accounts via OAuth; no Ethan-side API cost expected
- If costs appear: investigate `concerto-backend` for unexpected API calls

### 5.4 Churn and refund metrics

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT plan, status, COUNT(*) as n FROM concerto_buyers GROUP BY plan, status ORDER BY plan, n DESC;"
```

Flag if refund count >2/week or churn rate >10%.

### 5.5 Customer feedback synthesis

- Read all Discord `#feedback` messages from the past week
- Reply to at least one active customer with a personal email acknowledging their usage
- Document any feature request patterns in `MANAGER_STATE.md`

---

## 6. Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| Hosted droplets (concurrent) | 10+ | Create dedicated DO subaccount; separate billing from personal projects |
| Daily MCP relay requests | 25+ | Profile concerto-backend with `py-spy`; increase worker count in systemd unit `LimitNOFILE` |
| Total customers | 50+ | Hire VA for first-line Discord support; automate Discord moderation with Carl-bot auto-mod |
| Total customers | 100+ | Move SQLite → PostgreSQL on dedicated VPS; split empire into API + DB nodes |
| Empire CPU sustained >70% | — | Upgrade Hetzner VPS tier (CX21 → CX31, ~€2 more/month) |
| Status page outage >30 min | 3rd occurrence | Set up uptime monitoring with PagerDuty or BetterStack alert to phone |

---

## 7. Emergency Contacts and Account Recovery

### Cloudflare

- Login: cloudflare.com with Ethan's email
- If locked out: "Forgot password" → email recovery → 2FA via TOTP (backup codes stored in password manager)
- Zone ID: `208681448c90a193489a0907a48f6166`
- NS records: jonah + kiki.ns.cloudflare.com
- Cloudflare support: submit ticket at `support.cloudflare.com` (free plan: community only; Pro: ticket)

### DigitalOcean

- Login: cloud.digitalocean.com
- If locked out: DO account recovery via email
- Backup payment method: add a second credit card in DO billing
- API token is in `/etc/cortex/env` as `CONCERTO_DO_API_TOKEN`
- Sub-user delegation: DO → Settings → Team → invite a backup operator with limited scope

### Stripe

- Login: dashboard.stripe.com
- If locked out: Stripe recovery via phone/email 2FA
- Sub-user: Stripe → Settings → Team → invite with "Analyst" role for read-only access
- Webhook signing secret: stored in `/etc/cortex/env` as `STRIPE_WEBHOOK_SECRET`
- Live vs test mode: always confirm which mode you're in (banner at top of dashboard)

### NameSilo (DNS Registrar for concerto.run)

- Login: namesilo.com with Ethan's account
- Auth code (EPP code) needed for domain transfer: retrieve from NameSilo → Domains → Manage
- Auto-renewal: verify it's enabled so concerto.run doesn't expire
- Registrar lock: keep enabled to prevent unauthorized transfer

### Hetzner (Empire VPS)

- Login: `console.hetzner.cloud`
- VPS name: find by running `hostname` on the empire
- Console access (if SSH fails): Hetzner Console → Server → Console tab (VNC browser)
- Support ticket: console → Help → Support
- Firewall rules: Hetzner Firewall (allow 22, 8090 internal only; 80/443 via Cloudflare tunnel)
- Snapshot: Hetzner → Server → Snapshots → create manual snapshot before risky operations

---

## 8. Sample Customer Reply Templates

### 8.1 "Welcome, you're in!"

> Subject: You're live on Concerto — here's where to start
>
> Hey [Name],
>
> Your Concerto workspace is ready. Your dashboard is at: https://concerto.run/dashboard/[token]
>
> **Three things to do right now:**
> 1. Click "Connect Claude" on your dashboard to authorize Claude OAuth
> 2. Paste the MCP connector URL + token into claude.ai → Settings → Integrations
> 3. Try your first prompt — your fleet of agents is standing by
>
> If you hit any snag, join our Discord: [DISCORD_INVITE_URL] — I'm usually there within a few hours.
>
> Welcome aboard,
> Ethan

### 8.2 "We've issued your refund"

> Subject: Refund processed — sorry it didn't work out
>
> Hi [Name],
>
> I've issued a full refund of $[amount] to your card ending in [last4]. It typically appears within 5–10 business days depending on your bank.
>
> [If provisioning failed: "Your Concerto instance ran into a provisioning error — this was our fault, not yours."]
> [If policy refund: "No hard feelings — thanks for giving Concerto a try."]
>
> If you'd like to try again once [issue] is resolved, your next purchase will work fine — just use the same email.
>
> Best,
> Ethan

### 8.3 "Your droplet failed to provision — here's what happened and what we're doing"

> Subject: Concerto provisioning issue — action taken
>
> Hi [Name],
>
> Your Concerto instance ran into an error during provisioning. Here's what happened: [brief technical description, e.g., "DigitalOcean returned an error when creating your server — this is on their infrastructure side, not yours"].
>
> **What I've done:**
> - Destroyed the failed instance so you're not charged for DO resources
> - Issued a full refund of $[amount] to your payment method
>
> **What you can do:**
> - Wait a few hours and try again — the issue is usually transient
> - Reply to this email if you'd like me to manually retry provisioning for you at no charge
>
> Sorry for the friction. Concerto is in early access and I'm monitoring these closely.
>
> Ethan

### 8.4 "We saw your support request, looking into it"

> Subject: Re: [their subject] — on it
>
> Hi [Name],
>
> Got your message — I'm looking into it now. Typical turnaround is under 4 hours for anything infra-related.
>
> I'll follow up as soon as I have more info. If it's urgent, ping me on Discord: [DISCORD_INVITE_URL]
>
> Ethan

### 8.5 "Here's how to reset your Claude OAuth"

> Subject: Claude OAuth reset — steps to try
>
> Hi [Name],
>
> If your Claude OAuth connection is stuck, here's the fastest fix:
>
> 1. Go to your dashboard: https://concerto.run/dashboard/[token]
> 2. On Step 2, click "Disconnect" (if visible) then "Connect Claude" again
> 3. Make sure you're logging in with the account that has an **Anthropic Max plan** — OAuth requires Max
> 4. Try in an incognito/private browser window if it keeps failing
>
> If you've confirmed you have Max and it's still not working, reply here with a screenshot of the error and I'll dig in directly.
>
> Ethan

### 8.6 "Pricing question: Hosted vs BYOC"

> Subject: Re: pricing — hosted vs BYOC explained
>
> Hi [Name],
>
> Great question — here's the short version:
>
> **Hosted ($39/mo)**: Concerto provisions and manages a DigitalOcean server for you. Zero setup — your workspace is ready in minutes. We handle uptime, backups, and updates.
>
> **BYOC — Bring Your Own Cloud ($99 one-time)**: You point Concerto at your own DigitalOcean account. You own the infrastructure, pay DO directly (usually $6–12/mo for a small droplet), and have full control. No monthly fee to Concerto after the one-time purchase.
>
> **Which is right for you?**
> - Want the simplest path: Hosted
> - Want to own your infra + minimize recurring cost: BYOC (pays for itself after ~3 months)
>
> Let me know if you have follow-up questions.
>
> Ethan

---

## 9. Manual Operator Scripts

All commands run on the empire VPS. Adjust `CUSTOMER@EMAIL` and `<token>` as needed.

### Find buyer by email

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT id, email, plan, status, do_droplet_id, tunnel_url, first_call_at, created_at \
   FROM concerto_buyers WHERE email='CUSTOMER@EMAIL';"
```

### Show last 5 Stripe events

```bash
stripe events list --limit 5
```

### Check droplet status by buyer token

```bash
TOKEN=<buyer-token>
DROPLET_ID=$(sqlite3 /var/lib/concerto/concerto.db \
  "SELECT do_droplet_id FROM concerto_buyers WHERE token='$TOKEN';")
DO_TOKEN=$(grep CONCERTO_DO_API_TOKEN /etc/cortex/env | cut -d= -f2)
curl -s -H "Authorization: Bearer $DO_TOKEN" \
  "https://api.digitalocean.com/v2/droplets/$DROPLET_ID" \
  | python3 -m json.tool | grep -E '"status"|"name"|"networks"'
```

### Force re-send day-0 welcome email (drip runner)

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "UPDATE concerto_buyers SET drip_day_0_sent_at=NULL WHERE email='CUSTOMER@EMAIL';"
systemctl start concerto-drip-runner.service
# Check result:
journalctl -u concerto-drip-runner -n 20
```

### Manually mark buyer as refunded and destroy droplet

```bash
# Step 1: get droplet ID
DROPLET_ID=$(sqlite3 /var/lib/concerto/concerto.db \
  "SELECT do_droplet_id FROM concerto_buyers WHERE email='CUSTOMER@EMAIL';")
DO_TOKEN=$(grep CONCERTO_DO_API_TOKEN /etc/cortex/env | cut -d= -f2)

# Step 2: destroy droplet
curl -s -X DELETE \
  -H "Authorization: Bearer $DO_TOKEN" \
  "https://api.digitalocean.com/v2/droplets/$DROPLET_ID"

# Step 3: update DB
sqlite3 /var/lib/concerto/concerto.db \
  "UPDATE concerto_buyers \
   SET status='refunded', refunded_at=datetime('now'), do_droplet_id=NULL \
   WHERE email='CUSTOMER@EMAIL';"

# Step 4: issue Stripe refund manually via Dashboard (no CLI command — safer to click)
echo "Now go to: https://dashboard.stripe.com/payments — find payment, click Refund"
```

### Restart all Concerto services (after outage recovery)

```bash
for unit in concerto-backend concerto-hosted-lifecycle.timer concerto-drip-runner.timer concerto-status-writer.timer concerto-monitoring.timer; do
  systemctl reset-failed $unit 2>/dev/null
  systemctl restart $unit
  echo "$unit: $(systemctl is-active $unit)"
done
```

### Check all active hosted droplets

```bash
sqlite3 /var/lib/concerto/concerto.db \
  "SELECT email, do_droplet_id, status, tunnel_url, created_at \
   FROM concerto_buyers WHERE plan='hosted' AND status NOT IN ('refunded','cancelled') \
   ORDER BY created_at DESC;"
```

### Tail backend logs live

```bash
journalctl -u concerto-backend -f
```

---

*For strategic context on Concerto's current build state, see `/opt/cortex/OPS/MANAGER_STATE.md` (Phase CONCERTO-REBRAND and MAESTRO-OPERATOR-KIT sections). For support infra setup, see `docs/SUPPORT_SETUP.md`.*
