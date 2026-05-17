# Concerto — Copy Variants
*All variants ranked best-first. Final recommended combo marked ✅ FINAL.*
*Version: 2026-05-17 | Phase CONCERTO-LAUNCH*

---

## Hero Headlines
*5–9 words. No jargon. Ranked best-first.*

| # | Headline | Words | Angle |
|---|----------|-------|-------|
| 1 | **Claude Code on your cloud — from any browser.** | 9 | Ownership + access |
| 2 | **Your own Claude Code server, live in five minutes.** | 9 | Ownership + speed |
| 3 | **Run Claude Code anywhere. No terminal, no hassle.** | 8 | Liberation from friction |
| 4 | **Spin up a Claude Code agent. Just a browser.** | 9 | Ease + tool familiarity |
| 5 | **The missing remote for your Claude Max plan.** | 8 | Max-subscriber angle |

**Why #1 wins**: "Your cloud" signals ownership and privacy — the core differentiator vs. every competitor. "From any browser" signals access without terminal skill. The em-dash creates rhythm. It passes the 3-second test: you know what the product does and why it's different before reading the sub-headline.

---

## Sub-Headlines
*15–25 words. Answers "how?" and "what do I get?"*

| # | Sub-headline | Words | Angle |
|---|--------------|-------|-------|
| 1 | **Pay $99 once. Concerto provisions a Claude Code server in your DigitalOcean account and keeps it running — ready from any tab, any device.** | 25 | Price-forward + concrete mechanism |
| 2 | **Concerto turns your Claude Max subscription into an always-on cloud agent you can direct from any browser, on any project, any time.** | 24 | Max-subscriber leverage |
| 3 | **One payment, five minutes of setup, and Claude Code runs on a private VPS in your cloud — not ours.** | 21 | Anti-SaaS, ownership |
| 4 | **You own the Droplet. You own the data. Concerto handles the provisioning so you can handle the work.** | 18 | Sovereignty angle |
| 5 | **Claude Code doesn't have to live on your laptop. Concerto puts it on a server in your cloud account, open in your browser.** | 25 | Liberation angle |

**Why #1 wins**: Leads with the price (pre-empts sticker shock, signals one-time model), names the mechanism (DigitalOcean — concrete, not vague "cloud"), ends with the access promise. The dash creates rhythm without being coy.

---

## Feature Triplets
*3 variants. Each feature: 4-word headline + 12-word body. Ranked best-first.*

---

### Variant A — "Ownership First" ✅ RECOMMENDED

**Your Cloud, Your Rules**
Runs on a Droplet in your DigitalOcean account. Anthropic never touches your files.

**Any Browser, Zero Terminal**
Authenticate, monitor, and direct Claude Code from any tab. No SSH keys needed.

**Always On, Never Interrupted**
Your agent keeps working when you close the laptop. Pick up where it left off.

---

### Variant B — "Speed & Simplicity"

**Live in Five Minutes**
Concerto provisions your VPS, installs Claude Code, and opens a browser terminal automatically.

**Control From Any Device**
Phone, tablet, or laptop — your Claude Code agent answers from any browser tab.

**One Price, Zero Surprises**
Pay $99 once. Droplet costs go to your DigitalOcean — transparent, no markup, ever.

---

### Variant C — "Max Plan Leverage"

**Use Your Max Plan Fully**
You're already paying $100/month for Claude. Concerto puts it to work in the cloud.

**No Engineers Required**
Set up a production-grade Claude Code environment without touching a terminal or asking for help.

**Your Data Stays Yours**
Your VPS, your DigitalOcean account, your files. No shared infrastructure, no vendor data access.

---

## Pricing Card Variants
*3 variants. Ranked best-first.*

---

### Pricing Card A — Anchor Frame ✅ RECOMMENDED

**Concerto**
**$99** one-time

> Devin Pro: $200/month. Concerto: $99, once, forever.

What you get:
- Claude Code server provisioned in your DigitalOcean account
- Browser terminal — no SSH, no command line
- Always-on: your agent runs while you sleep
- Your Claude Max plan powers the AI — no new subscription

*You pay DigitalOcean directly (~$24/mo for a 2vCPU/4GB Droplet). We never touch your cloud bill.*

**[Deploy your agent — $99]**

*Why this wins*: Anchors against Devin's $200/mo (a name the buyer knows). Makes $99 one-time feel cheap by comparison. Transparent about Droplet cost removes the fear of hidden fees.

---

### Pricing Card B — Value Frame

**Concerto**
**$99** one-time

> An always-on AI coding agent for the price of lunch, every month.

$99 ÷ 12 months = **$8.25/month** amortized.
Add your Droplet (~$24/mo to DigitalOcean) = **$32/month total**.

Compare: Devin Pro ($200/mo), Replit Pro ($95/mo), Cursor Teams ($40/user/mo).
Concerto is the only one that runs on *your* cloud and uses *your* Claude Max plan.

**[Start in 5 minutes]**

---

### Pricing Card C — "Why $99" Pre-empt

**Concerto**
**$99** one-time

**Why $99?**
Your VPS runs in your DigitalOcean account — we never host your code or your agent. The $99 covers: our provisioning API, the installer, the web terminal proxy, and ongoing updates to the stack. After that, your costs are your Droplet (~$24/mo, billed directly to your DO account) and your Claude Max plan.

No subscription. No per-seat fees. No token markup.

**[Get Concerto]**

*Why this wins for skeptics*: Directly addresses the "what am I actually paying for?" doubt that every sophisticated buyer has. Transparency converts the skeptic who would otherwise bounce.

---

## FAQ — Questions Buyers Actually Ask

*These are not generic SaaS FAQ questions. They reflect the specific anxieties of someone considering "letting an AI run on my VPS."*

---

**1. What if Claude Code does something destructive to my Droplet — overwrites a file, runs a bad command, or fills the disk?**

Claude Code runs with access only to the directories you specify. Nothing in the Concerto setup gives Claude Code system-wide write access. That said — the VPS is in your DigitalOcean account, which means you have full root access, snapshots, and DigitalOcean's "Destroy Droplet" button as a nuclear option. We recommend taking a DO snapshot before any large refactor, same as you'd commit before a big change.

---

**2. Can Concerto or Anthropic see my files? What happens to my code?**

Concerto cannot see your files. The VPS runs in your DigitalOcean account — we provision it, then we're done. We maintain a Cloudflare tunnel for the browser terminal, but that tunnel is scoped to your session token and carries no file access. Your Claude Code conversations go directly from your VPS to Anthropic's API via your Claude Max plan. Anthropic's data handling policies apply, same as when you use Claude Code locally.

---

**3. I already pay $100/month for Claude Max. Is Concerto another subscription on top of that?**

No. Concerto is $99 one-time. After that, the only recurring costs are: (a) your Claude Max subscription, which you already have, and (b) your DigitalOcean Droplet (~$24/month), billed directly to your DO account. Concerto charges you nothing monthly. We're the plumber, not the landlord.

---

**4. What does "$99 one-time" actually cover? What am I paying for monthly after that?**

The $99 covers: our provisioning API (which calls DigitalOcean to create and configure your Droplet), the installer script (which sets up Claude Code, the MCP server, and the secure tunnel), the browser terminal (the web interface for one-time Claude auth), and all future updates to the Concerto installer stack. Monthly after that: your DigitalOcean Droplet (~$24/month, billed to your DO account) and your Claude Max plan. No Concerto subscription, ever.

---

**5. What if I don't have a DigitalOcean account? Can I use AWS, Hetzner, or my own server?**

V1 requires a DigitalOcean account (free to create, no minimum spend). We use their API to provision your Droplet automatically — that's what makes the 5-minute setup possible. Hetzner support is planned for v2. AWS/GCP/Azure support depends on demand. If you have an existing VPS you'd like to use, check our docs for the manual installer path (requires SSH access and ~15 minutes).

---

**6. What happens if I want to cancel? Can I delete the Droplet and get a refund?**

You can destroy your Droplet in your DigitalOcean dashboard at any time — you control it completely. DigitalOcean stops billing you the moment it's destroyed. As for the $99: we offer a 7-day full refund if the provisioning fails or Concerto doesn't work as described. If you've successfully provisioned and used the product, the $99 is non-refundable — it covers the one-time setup work.

---

**7. How is this different from just SSH-ing into a server myself and running Claude Code?**

If you're comfortable with SSH, Linux, npm, OAuth flows, and Cloudflare tunnel configuration — you can absolutely do it yourself. It takes 2–3 hours the first time and about 45 minutes each time you spin up a new machine. Concerto does all of that in 5 minutes, with a web terminal so you don't need to babysit an SSH session. The $99 is the price of not spending a Friday afternoon on DevOps when you could be building. If your time is worth more than $33/hour, the math works on the first use.

---

## Call-to-Action Variants
*3 above-fold CTA variants. Ranked best-first.*

| # | CTA text | Tone | When to use |
|---|----------|------|-------------|
| 1 | **Deploy your agent — $99** | Price-forward, confident | Primary hero CTA. Shows price upfront, filters unqualified visitors. |
| 2 | **Set up in 5 minutes** | Speed-forward, low-friction | A/B test after video or demo — lower commitment entry point. |
| 3 | **Get Concerto** | Clean, minimal | Nav bars, repeat CTAs lower on page, email campaigns. |

**Why #1 wins for above-fold**: Showing the price in the CTA filters visitors who aren't serious, increasing conversion quality. "$99" in a button signals "one-time transaction" not a subscription trap — reducing checkout anxiety.

---

## ✅ FINAL RECOMMENDED COMBO

```
Hero headline:      "Claude Code on your cloud — from any browser."

Sub-headline:       "Pay $99 once. Concerto provisions a Claude Code server in your
                    DigitalOcean account and keeps it running — ready from any tab,
                    any device."

Feature triplet:    Variant A — "Ownership First"
                    1. Your Cloud, Your Rules
                    2. Any Browser, Zero Terminal
                    3. Always On, Never Interrupted

Pricing card:       Card A — Anchor Frame (Devin $200/mo vs. Concerto $99 once)

Primary CTA:        "Deploy your agent — $99"
Secondary CTA:      "Set up in 5 minutes"

FAQ order:          All 7 in sequence as written above
```

**Rationale**: Hero + sub establish what it does and how it prices in one read. Variant A features reinforce the ownership angle (the structural moat). The Devin anchor pricing card converts buyers who have shopped alternatives. The price-forward CTA filters for intent and reduces checkout anxiety. The 7 FAQ questions destroy the objections that kill conversions silently — especially questions 1, 2, and 4, which are the "letting an AI run on my server" anxieties that have no analogue in SaaS FAQ templates.

---

*End of Copy Variants*
