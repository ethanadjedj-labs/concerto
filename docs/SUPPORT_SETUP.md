# Maestro Operator Support Setup Runbook

This document covers everything you need to stand up support infrastructure for Maestro: Discord community, support email routing, and auto-responder templates.

---

## 1. Discord Server — "Maestro Operators"

### 1.1 Create the server

1. Open Discord → "+" (Add a Server) → **Create My Own** → **For a club or community**.
2. Server name: **Maestro Operators**. Upload the Maestro logo as the icon.
3. Delete the auto-created `#general` channel — you'll replace it with the channels below.

### 1.2 Channel structure

Create channels in this order (click "+" beside "TEXT CHANNELS"):

| Channel | Purpose |
|---------|---------|
| `#announcements` | Product updates, new features, maintenance windows. **Read-only for members.** |
| `#welcome` | First channel members see. Pinned post explains roles + where to go. |
| `#help` | Main support channel. Members ask questions; team replies. |
| `#show-and-tell` | Members share workflows, prompts, and results. |
| `#feature-requests` | Structured feature requests. Consider a bot to collect upvotes. |

**Category layout** (drag channels into categories):
```
📢 ANNOUNCEMENTS
   #announcements
👋 COMMUNITY
   #welcome
   #show-and-tell
   #feature-requests
🛠️ SUPPORT
   #help
```

### 1.3 Roles

Create two member roles under **Server Settings → Roles**:

| Role | Color | Permissions | Assignment trigger |
|------|-------|-------------|-------------------|
| `Hosted` | Violet (#7c3aed) | Read all channels, send messages | Stripe webhook: `price_1TY4q2AIsRiuuZrfI7yr2gBw` (monthly plan) |
| `BYOC` | Indigo (#4f46e5) | Read all channels, send messages | Stripe webhook: `price_...` (one-time $99) |

**Role auto-assignment via Stripe webhook** (pending implementation):
When a `checkout.session.completed` webhook fires, the backend should POST to the Discord API:
```
PUT /guilds/{GUILD_ID}/members/{DISCORD_USER_ID}/roles/{ROLE_ID}
Authorization: Bot {DISCORD_BOT_TOKEN}
```
This requires collecting the buyer's Discord username during onboarding (add field to `/setup/{token}` page). Until that is wired, assign roles manually via server member list.

### 1.4 Bot setup (Carl-bot — free tier)

1. Visit https://carl.gg → "Invite" → select **Maestro Operators** server.
2. Grant permissions: Manage Roles, Manage Messages, Read/Send Messages, Embed Links.
3. In Carl-bot dashboard → **Autoroles**: set `Hosted` to auto-assign on join (temporary default until Stripe webhook is live).
4. In Carl-bot dashboard → **Welcome**: set #welcome as the welcome channel. Template:
   ```
   Welcome {mention}! You've joined the Maestro Operators community.
   • Check #welcome for orientation
   • Ask questions in #help
   • Share what you build in #show-and-tell
   ```
5. **Automod** (optional): enable anti-spam and block invite links in #help.

Alternative: **MEE6 free tier** (mee6.xyz) — similar feature set. Carl-bot has a better free tier for role automation; MEE6 has a cleaner moderation dashboard. Either works.

### 1.5 Invite link generation

Server Settings → **Invites** → Create Invite:
- Channel: `#welcome`
- Expiry: **Never**
- Max uses: **Unlimited**
- Copy the link. Use this URL everywhere: in onboarding emails, the dashboard, and the landing page.

Persist the invite URL: add `DISCORD_INVITE_URL` to `/etc/cortex/env` and Vercel env vars.

### 1.6 Basic moderation

- In **#announcements**: edit channel permissions → remove "Send Messages" from `@everyone`. Keep it for `@Moderator` or `@Admin` only.
- Pin a welcome message in `#welcome` explaining the server structure.
- Appoint a moderator role early; Discord's built-in timeout (right-click → Timeout) handles most issues.

---

## 2. Support Email — support@maestro.run

### 2.1 DNS prerequisite

`maestro.run` must be acquired and delegated to Cloudflare before email can be configured. See [pending operator action #1 in MANAGER_STATE.md].

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
2. Add domain `maestro.run`. Migadu will show you MX, SPF, DKIM, DMARC records.
3. In Cloudflare (zone `d4f729f470a0804a4ef89ff0dc8281ad`), add:
   - `MX maestro.run → aspmx1.migadu.com` (priority 10)
   - `MX maestro.run → aspmx2.migadu.com` (priority 20)
   - `TXT maestro.run → "v=spf1 include:spf.migadu.com ~all"`
   - `TXT _dmarc.maestro.run → "v=DMARC1; p=quarantine; rua=mailto:dmarc@maestro.run"`
   - `CNAME key1._domainkey.maestro.run → key1.maestro.run._domainkey.migadu.com`
4. Create mailbox: `support@maestro.run` (forward to `adjedjethan@gmail.com` or team inbox).
5. Create alias: `noreply@maestro.run` → discard (for transactional email From address).

### 2.3 Option B — Resend Inbound (alternative)

**Cost**: Free tier (100 inbound/day); $20/mo for higher volume.

**Pros**:
- Already integrated with transactional outbound (Resend API key in `/etc/cortex/env`)
- Webhook-based inbound — easy to wire into a Slack notification or ticket system
- Same dashboard for inbound + outbound

**Cons**:
- No native IMAP — replies must be sent via Resend API or a separate SMTP provider
- Inbound webhooks require a public endpoint to receive tickets
- More expensive at volume vs Migadu

**Setup**: Resend dashboard → Domains → `maestro.run` → Inbound → enable. Point MX to Resend's servers. Configure webhook URL: `https://api.maestro.run/webhooks/inbound-email`.

### 2.4 Recommendation

**Use Migadu**. At $19/yr it costs less than one month of Resend paid. Inbound email for a support channel does not need real-time webhooks at launch — a daily email review is sufficient. Migrate to Resend Inbound later if you want ticket automation.

---

## 3. Auto-Responder Templates

When a support email arrives at `support@maestro.run`, an auto-responder should acknowledge receipt immediately.

### 3.1 English template

**Subject**: `Re: {{original_subject}} — We received your message`

```
Hi,

Thanks for reaching out to Maestro support. We've received your message and will get back to you within 24 hours (usually sooner).

While you wait, you might find an answer in our:
• Help center: https://maestro.run/help
• Community Discord: {{discord_invite_url}}

— The Maestro team
support@maestro.run | https://maestro.run
```

### 3.2 French template

**Subject**: `Re: {{original_subject}} — Votre message a bien été reçu`

```
Bonjour,

Merci de nous avoir contacté. Votre message a bien été reçu et nous vous répondrons dans les 24 heures (souvent plus tôt).

En attendant, vous trouverez peut-être une réponse dans :
• Notre centre d'aide : https://maestro.run/help
• Notre communauté Discord : {{discord_invite_url}}

— L'équipe Maestro
support@maestro.run | https://maestro.run
```

### 3.3 Implementation

Migadu supports auto-responders natively under mailbox settings → **Vacation / Auto-Reply**. Paste the EN template there. For bilingual detection (based on sender IP or email language headers), a lightweight Cloudflare Worker could route and reply — skip this until volume justifies it.

---

## 4. MANAGER_STATE Pending Actions

Add these to the pending operator actions list:

- [ ] **Acquire maestro.run** and delegate NS to Cloudflare (prerequisite for all email setup)
- [ ] **Migadu**: sign up, add domain, add DNS records in Cloudflare, create `support@maestro.run` mailbox
- [ ] **Discord**: create server, configure channels, generate permanent invite link, store as `DISCORD_INVITE_URL` env var
- [ ] **Carl-bot**: invite, configure autorole + welcome message
- [ ] **Stripe webhook**: wire Discord role assignment when buyer Discord username is collected
- [ ] **status.maestro.run DNS**: add CNAME → Vercel (once status page is deployed)
