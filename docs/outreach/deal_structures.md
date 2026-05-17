# Concerto Deal Structures
*Three concrete proposals for creator + B2B partnerships — May 2026*

---

## A. Creator Affiliate Program

### Structure
Code-based referral tracking via **Rewardful** (Starter plan, $49/mo — see tooling section below).

Each creator receives:
- Unique referral link + optional promo code (e.g., `INDYDEVDAN`)
- **Hosted tier (recurring):** 20% recurring revenue share = **$7.80/month per active Hosted customer, lifetime of subscription** ($39/mo × 20%)
- **BYOC tier (one-time):** 30% of $99 one-time = **$29.70 per sale**
- Real-time dashboard showing clicks, trials, conversions, and monthly payouts
- PayPal or Wise payout, minimum $50 threshold

### Example Payouts
| Scenario | Monthly Earnings |
|---|---|
| 10 active Hosted subs referred | $78/mo ($936/yr) |
| 50 active Hosted subs referred | $390/mo ($4,680/yr) |
| 100 active Hosted subs referred (top creator) | $780/mo ($9,360/yr) |
| 20 BYOC sales/month | $594/mo one-time |

### Tooling: Rewardful (Top Pick)

**Why Rewardful:**
- Stripe Premier Partner — deepest native Stripe integration; no code changes beyond a JavaScript snippet
- Auto-adjusts commissions on refunds, cancellations, and upgrades (critical for subscription integrity)
- Handles both Hosted ($39/mo subscription) and BYOC ($99 one-time) natively
- 0% transaction fees (all plans)
- Unlimited affiliates on all plans
- SEO-friendly links (no ugly redirects)

**Pricing:**
- Starter: **$49/mo** — covers up to $7,500/mo in affiliate-driven revenue, unlimited affiliates
- Growth: **$99/mo** — up to $15,000/mo, branded portal with custom domain, multiple campaigns
- Upgrade threshold: When affiliate-driven MRR consistently exceeds ~$5,000/mo

**Setup:** ~15-20 minute setup ("5 steps"), no developer required. JavaScript snippet + Stripe webhook.

**Alternatives evaluated:**
- **Tolt ($69/mo):** Also strong, slightly higher price, 2% payout fee on Growth tier, clean UI
- **FirstPromoter ($49/mo):** Solid fallback, slightly dated UX vs Rewardful
- **Reflio:** Open-source indie tool, pricing page errors (May 2026), reliability risk — not recommended
- **Lemon Squeezy:** Full payment processor replacement (5%+3%+fees), would require dropping Stripe — not recommended
- **PartnerStack:** Enterprise ($800+/mo) — vastly overbuilt for current stage

### Pros
- Zero upfront cost to creator — they earn only on conversion
- Lifetime recurring commission creates long-term alignment
- Automated via Rewardful — no manual tracking or payout calculation
- Scales naturally: top creators earn more as their audience grows

### Cons
- Lower upfront incentive than paid sponsorship — requires creators to have conviction in the product
- No guaranteed exposure; a creator may activate but not promote actively
- Requires product quality that earns organic mentions (can't just pay for placement)

### When to Use
Use affiliate-first for creators who are **genuine Claude Code users** and whose audience is developers. Reserve affiliate-only (no cash upfront) for Priority 1 and 2 creators who will use the product anyway. Combine with free Pro account + Hosted credits to reduce friction.

---

## B. Sponsored Content / Paid Promotion

### Rate Card

#### Tier 1: >100K subscribers/followers

| Format | Rate |
|---|---|
| Dedicated video (full review or tutorial) | $1,500 – $3,000 |
| "Tools I'm using" segment (1-3 min) | $500 – $1,000 |
| Newsletter dedicated issue | $800 – $2,000 |
| Newsletter mention/segment | $200 – $500 |

*Applicable to: Fireship (4.1M YT), Traversy Media (2.4M YT), Theo t3.gg (398K YT), Nate Herk (750K YT), Programming with Mosh (4.2M YT), Matt Pocock (268.9K X + 199K YT), Natesnewsletter (150K Substack)*

#### Tier 2: 10K – 100K subscribers/followers

| Format | Rate |
|---|---|
| Dedicated video | $300 – $800 |
| "Tools I'm using" segment | $100 – $300 |
| Newsletter dedicated issue | $150 – $400 |
| Newsletter mention | $50 – $150 |
| Twitter thread sponsorship | $200 – $500 |

*Applicable to: IndyDevDan (127K YT), Jack Herrington (162K YT), Grace Leung (127K YT), swyx (121.9K X), Simon Willison (132.4K X), Karo Zieminski (17K Substack), Wyndo AI Maker (19K Substack)*

#### Tier 3: <10K but engaged — Free product exchange

| What Concerto provides | What creator provides |
|---|---|
| Free Pro account (lifetime) | Review video, blog post, or Twitter thread |
| Hosted credits ($100-500 value) | Honest public feedback (positive or critical) |
| Early access to new features | Participation in beta feedback sessions |
| Co-marketing mentions | User testimonial |

*Applicable to: Chris Raroque (75-85K YT — offer Tier 2 + free product), Yifan BTH, Ray Amjad, Maham Codes, Primal Rationalist, Florian Bruniaux, Povilas Korop, Nick Dobos*

### Sponsored Content Requirements (Brief)
All paid placements must:
1. Include honest disclosure ("sponsored by Concerto")
2. Use the creator's authentic voice — no mandated scripts
3. Include a verifiable URL or promo code for tracking
4. Allow Concerto right to share/re-use the content organically

### Pros
- Guaranteed exposure regardless of product conviction
- Predictable cost for planning/forecasting
- Tier 1 videos can generate 50K-500K+ views

### Cons
- No performance alignment — creator earns same whether 0 or 1,000 conversions
- Can feel inauthentic if creator hasn't actually used the product
- Cash outlay upfront with variable ROI

### When to Use
Use paid sponsorship for **brand awareness** phase (pre-SEO, pre-word-of-mouth). Target Tier 1 channels for broad reach, Tier 2 for developer-segment credibility. Never pay Tier 1 rates without product access period first — give free account 2-4 weeks before recording.

---

## C. Co-Marketing / Strategic Partnership

### For: Power creators + B2B prospects with aligned audiences

This structure works for partners who have both audience AND product alignment — not just exposure.

### Components

#### For Power Creators (Matt Pocock, IndyDevDan, swyx):
1. **Free tier for them + their team** (all seats, full Hosted access)
2. **Co-authored case study** — their Claude Code workflow + Concerto as the runtime infrastructure
3. **Mutual feature input** — creator joins early access / advisory track, shapes roadmap
4. **Cross-promotion** — Concerto featured in their newsletter/podcast + creator featured in Concerto's blog/social
5. **Optional:** revenue-share on course bundles (e.g., Matt Pocock's "Claude Code for Real Engineers" + Concerto Pro = bundled offer)

#### For B2B Partners (HumanLayer, Graphite, Embedder):
1. **Free team accounts** — all engineers, Hosted tier
2. **Technical integration** — Concerto as session layer in their product stack (API access, webhook integration)
3. **Co-authored technical post** — published on both company blogs + shared on social
4. **Mutual product page links** — "Works with Concerto" badge in their docs / "Works with HumanLayer" in ours
5. **Joint conference/webinar** — co-present at AI Engineer, YC Demo Day adjacent events

### Investment Required
- Free accounts: ~$39/mo × N seats (at near-zero marginal cost until Hosted servers fill up)
- Engineering time for integrations: 2-5 days per integration (if any)
- Content time: 4-8 hours per co-authored piece

### Pros
- Highest long-term value — creates ecosystem lock-in
- Feels earned and authentic to both parties' audiences
- Partner's audience trusts them → trust transfers to Concerto
- Integration partners drive product-qualified leads (users who already understand the stack)

### Cons
- Requires existing relationship credibility or strong product-market fit
- Slower to execute (weeks/months vs days for paid placements)
- Requires both parties to invest time

### When to Use
Deploy strategic partnerships for **top-5 creators** and **top-3 B2B partners** after initial outreach confirms product fit. Scale paid sponsorships in parallel for broad awareness while deep partnerships develop over 30-90 days.
