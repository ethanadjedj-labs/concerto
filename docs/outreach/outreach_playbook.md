# Concerto Outreach Playbook
*Templates, sequencing, tracking, and anti-patterns — May 2026*

---

## 1. Recommended Outreach Order

### Phase 1 (Week 1-2): Creators First
**Why creators first:**
- Smaller universe, faster feedback loops (days not weeks)
- Success stories from creators warm B2B inbound (proof via video = social proof)
- Creator referrals generate trackable revenue within 30-60 days
- Lower relationship overhead than enterprise sales cycles

**Sequencing within creators:**
1. Priority 1 creators via Twitter DM (IndyDevDan, Matt Pocock, Theo, Chris Raroque, Simon Willison, Nick Dobos, Nate Herk)
2. Priority 2 creators — paid sponsorship discussion (Fireship, Traversy, swyx, Jack Herrington)
3. Priority 3 creators — free product exchange + affiliate
4. Tier 3 (high-engagement, small audience) — free account, no ask

### Phase 2 (Week 2-4): B2B Parallel Track
**Why parallel, not sequential:**
- B2B sales cycles are 4-12 weeks even for small companies
- Starting B2B outreach during creator phase gives time for first conversations to develop while creator content is being created
- YC startups (HumanLayer, Ambral, Vulcan, Embedder) are accessible and fast to close

**Sequencing within B2B:**
1. YC startups (Priority 1) — founders are reachable via YC founder network, Twitter, email
2. Mid-market dev-tools (Priority 1-2) — Sanity, Treasure Data, Wordsmith AI, Nevis
3. Larger companies (Priority 3) — Intercom, Ramp, Shopify — target internal champions, not C-suite

---

## 2. Message Templates

### Creator Templates

#### Template C1 — Twitter DM (Priority 1, Affiliate-First)
For: IndyDevDan, Matt Pocock, Chris Raroque, Simon Willison, Nick Dobos

> **[Creator first name]** — quick note: we built Concerto, a managed operator layer for Claude Code teams. [1 specific reference to their content that shows you actually watched it]. We think it fits your workflow / audience well. Free Pro + Hosted credits to try, no strings. If it clicks, we have an affiliate program — 20% recurring on Hosted ($7.80/mo per sub, lifetime) + 30% on BYOC sales. No obligation to promote if it doesn't resonate. Want to try it?
>
> — Ethan @ concerto.run

*Personalization slot: Replace [1 specific reference] with e.g. "Your Elite Context Engineering video is the closest thing to a product spec I've seen." or "Your Boris Cherny interview was one of the best pieces on Claude Code's philosophy."*

#### Template C2 — Twitter DM (Priority 2, Sponsorship-First)
For: Fireship, Traversy Media, Nate Herk, Jack Herrington

> **[Creator first name]** — love the Claude Code content. We're Concerto — managed session layer for Claude Code fleets. We'd love to explore a sponsored segment in your "[specific video series or format]." Rate card: $500-1000 for a tools segment, $1500-3000 for dedicated. Free product access first so you can speak honestly. What's the best way to discuss a sponsorship with your team?
>
> — Ethan @ concerto.run

#### Template C3 — Email (Substack creators, bloggers)
For: Nate's Newsletter, Wyndo AI Maker, Karo Zieminski, Povilas Korop, Freek Van der Herten

**Subject:** Concerto sponsorship / affiliate — [creator's newsletter name]

> Hi [Name],
>
> I'm Ethan, building Concerto (concerto.run) — the managed operator layer for Claude Code. Your [newsletter/blog] is one of the best resources covering Claude Code adoption I've come across, and your audience is exactly who we're building for.
>
> Quick ask: would you be open to either:
> (a) A sponsored edition ($150-400 for a segment, $800-2000 for a dedicated issue), or
> (b) An affiliate arrangement — 20% recurring commission on every Hosted subscriber you refer ($7.80/mo lifetime), tracked via unique link?
>
> Free Pro + Hosted access included either way so you can write from experience.
>
> Happy to answer any questions or send a product brief. Is this something you'd consider?
>
> — Ethan Adjedj | Concerto

#### Template C4 — Tier 3 (Free Product, No Cash Ask)
For: Ray Amjad, Primal Rationalist, Maham Codes, Florian Bruniaux, GitHub creators

> **[Handle]** — big fan of [specific content]. We'd love to offer you a free Concerto Pro account (full Hosted access) — no ask attached. We just think you'd find it useful for [specific use case relevant to their content]. If you want to share thoughts publicly at some point, we'd love that, but genuinely no pressure.
>
> — Ethan @ concerto.run

---

### B2B Templates

#### Template B1 — LinkedIn InMail (Priority 1, YC Startups)
For: Dexter Horthy (HumanLayer), Jack Stettner (Ambral), Ethan Gibbs (Embedder)

**Subject:** Concerto + [Company] — team-level Claude Code infrastructure

> Hi [Name],
>
> I'm Ethan, building Concerto — the managed session layer for teams running Claude Code at scale. [One specific sentence about their Claude Code usage — reference blog post, YC page, or Anthropic feature.]
>
> We're offering free Hosted accounts for the [Company] engineering team — no pitch attached, just think the product fit is real and would love your honest feedback.
>
> If there's interest in a longer conversation about team-level session management, happy to jump on a 15-min call.
>
> — Ethan | concerto.run

#### Template B2 — Cold Email (Priority 1-2, Mid-Market)
For: Sanity, Treasure Data, Wordsmith AI, Nevis, Graphite

**Subject:** Concerto pilot — team-level Claude Code for [Company Engineering] team

> Hi [Name],
>
> I'm Ethan, founder of Concerto (concerto.run). We build the managed operator layer for engineering teams that have adopted Claude Code — session lifecycle management, context persistence, BYOC or Hosted options.
>
> [Company]'s [specific signal — blog post, customer story, public mention] caught my attention: [one sentence about what they published]. Teams at that stage of adoption are exactly who Concerto is built for.
>
> We'd love to offer a free pilot for your engineering team — 30-day full access, no commitment. Happy to start with a 20-min call to understand your current workflow.
>
> — Ethan Adjedj | Concerto | ethan@concerto.run

#### Template B3 — Twitter DM (Priority 2-3, Individual Champions)
For: Brian Scanlan (Intercom), Farhan Thawar (Shopify), Beyang Liu (Sourcegraph)

> **[Name]** — your work on [specific thing — "Intercom's 2x PR velocity with Claude Code" / "Shopify's AI-first engineering"] is one of the best documented Claude Code adoptions I've seen. We built Concerto to handle the infrastructure layer teams need after that initial adoption: session management, context routing, team visibility. Would love to show you what we've built — 20 minutes?
>
> — Ethan @ concerto.run

---

## 3. Tracking: Notion/Airtable Schema

### Master Outreach Table

| Field | Type | Values |
|---|---|---|
| Name | Text | Creator/company name |
| Handle | Text | Primary handle |
| Type | Select | Creator / B2B |
| Platform | Select | YouTube / X / LinkedIn / Email / GitHub |
| Priority | Number | 1-5 |
| Status | Select | Not contacted / Contacted / Replied / Call scheduled / In negotiation / Activated / Declined / No response |
| Contact Date | Date | YYYY-MM-DD |
| Last Activity | Date | YYYY-MM-DD |
| Channel | Select | Twitter DM / Email / LinkedIn / YouTube DM |
| Deal Type | Select | Affiliate / Sponsored / Partnership / B2B pilot / Free product |
| Affiliate Code | Text | e.g., INDYDEVDAN |
| Revenue Share | Number | % (for affiliates) |
| Agreed Rate | Currency | $USD (for sponsorships) |
| Referrals | Number | Count of referred customers |
| MRR Generated | Currency | Monthly recurring from their referrals |
| Notes | Text | Last message, key context |

### Creator Affiliate Sub-table (linked to Rewardful)

| Field | Source |
|---|---|
| Referral Link | Rewardful auto-generate |
| Clicks | Rewardful dashboard |
| Trials Started | Rewardful dashboard |
| Conversions | Rewardful dashboard |
| Active Subs | Rewardful dashboard |
| Pending Payout | Rewardful dashboard |
| Last Payout | Rewardful dashboard |

### Monthly Review Checklist
- [ ] Review all Rewardful affiliate dashboards — flag any creator with >10 clicks but 0 conversions (possible tracking issue or landing page problem)
- [ ] Follow up on anyone in "No response" status after 14 days (one follow-up only)
- [ ] Activate payout for all affiliates above $50 threshold
- [ ] Update "Status" for all B2B prospects with activity in last 30 days
- [ ] Review any new Claude Code creators who emerged in the month (set Google Alert: "Claude Code" site:youtube.com)

---

## 4. Anti-Patterns: What NOT to Do

### ❌ Mass blast
Never send the same template to 30+ creators without personalization. DMs with zero personalization get ignored and damage the Concerto brand. Every message needs at least one sentence showing you know their work.

### ❌ Name-drop without permission
Never say "Stripe uses Claude Code, so you should use Concerto." That's not a logical leap, and Stripe hasn't endorsed Concerto. Only reference companies/creators who have explicitly agreed to be referenced.

### ❌ Claim product features that don't exist yet
Be honest about Concerto's current feature set. If multi-agent orchestration is on the roadmap but not shipped, say "on roadmap" — don't imply it exists. Creators with technical audiences will test claims.

### ❌ Chasing follower count without audience alignment
Paying $2,000 for a segment to a 500K-sub channel whose audience is cryptocurrency traders will underperform a $200 segment to a 20K developer-focused channel. Audience profile > audience size.

### ❌ Asking before giving
Always lead with the free account / free product. Don't ask for a review, post, or promotion in the first message. Give first, ask later — this earns authentic advocacy rather than transactional compliance.

### ❌ Following up more than once on silence
One follow-up after 7-10 days of silence is acceptable. Two is the maximum. After that, mark as "No response" and move on. Aggressive follow-up hurts the brand.

### ❌ Offering affiliate to someone with no relevant audience
Affiliates only make sense for creators whose audience would actually use Concerto. Offering an affiliate code to a crypto influencer whose audience is traders produces noise, not revenue.

### ❌ Combining ask + money pressure
Never say "we have a limited budget" or "this offer expires [date]" in cold outreach. Artificial scarcity in creator/B2B outreach feels manipulative and damages trust from the first message.

### ❌ Skipping the product-experience step for sponsored content
Always give the creator free product access before they record any sponsored content. A sponsor who hasn't used the product will produce stiff, unconvincing content, and their audience will notice.
