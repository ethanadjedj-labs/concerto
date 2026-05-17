# Refund Policy

**Maestro** — Remote Workshop for Claude Code Agents

_Last updated: 2026-05-17_

---

## The Short Version

- **Full refund**: if your Droplet never reached "ready" and it's been fewer than 14 days since you purchased.
- **No refund**: once your Droplet is successfully provisioned (you can access it in the dashboard), the service has been rendered.
- **How to claim**: email **support@maestro.run** from your purchase email address.
- **Timeline**: Stripe processes refunds within 5 business days of approval.

---

## Full Details

### When you are entitled to a refund

You qualify for a **100% refund of $99.00 USD** if all of the following are true:

1. Your purchase was made within the last **14 calendar days**.
2. Your Droplet status in the Maestro dashboard shows something other than **"ready"** — meaning the provisioning process did not complete successfully (stuck in "provisioning," "error," or "pending").
3. You have not manually modified or deleted the Droplet in your DigitalOcean account in a way that prevented provisioning (e.g., deleted the DO API key before provisioning completed).

We will issue the refund without argument. Provisioning is our job; if we failed at it, you owe us nothing.

### When a refund is not available

Once your Droplet shows **"ready"** status in the dashboard, the service has been delivered. At that point:

- A Droplet is running inside your DigitalOcean account
- Claude Code is installed and accessible via the browser terminal
- The $99 fee covers the provisioning and orchestration work, which has been completed

Because the Droplet itself is in your DigitalOcean account — not ours — we cannot "take it back." The refund window exists precisely for the case where we failed to deliver, not for change-of-mind after a successful setup.

### Edge cases

**Provisioning partially completed, then stalled**: If the Droplet was created in your DO account but never reached "ready" (e.g., cloud-init failed, tunnel never connected), this counts as a provisioning failure. You are entitled to a full refund. The Droplet in your DO account is yours to delete.

**Refund request after 14 days**: We will consider late refund requests for provisioning failures on a case-by-case basis. Email us — if we genuinely failed, we'll make it right.

**Chargeback**: If you initiate a credit card chargeback before contacting us, it may prevent us from processing a refund and may result in suspension of your Maestro access. Please email us first — we resolve disputes quickly.

---

## How to Request a Refund

1. Email **support@maestro.run** with the subject line: `Refund request — [your purchase email]`
2. Include: your purchase email address and a brief description of what went wrong (optional but helpful for us to fix it)
3. We will respond within 1 business day to confirm eligibility
4. Once approved, Stripe processes the refund to your original payment method within **5 business days**

---

## Contact

**Email**: support@maestro.run
