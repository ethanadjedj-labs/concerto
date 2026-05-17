# Terms of Service

**Concerto** — Remote Workshop for Claude Code Agents

_Last updated: 2026-05-17_

---

## 1. Who We Are and What Concerto Does

Concerto is a provisioning and orchestration service operated by Ethan Adjedj ("we," "us," "our"). When you purchase access to Concerto, we use your DigitalOcean API key to spin up a Virtual Private Server (VPS) — a Droplet — inside **your** DigitalOcean account. We then install Claude Code, an MCP server, and a secure tunnel so you can pilot Claude Code agents from your browser.

Key point: **you own the infrastructure.** The Droplet lives in your DigitalOcean account, is billed by DigitalOcean directly to you, and you retain full control over it. Concerto's role is to provision it, connect you to it, and get out of your way.

---

## 2. The Service in Plain Terms

- **What you pay us**: a one-time fee of **$99 USD**, processed by Stripe.
- **What you get**: a ready-to-use remote Claude Code workshop running on a DigitalOcean Droplet in your account.
- **What remains yours**: the Droplet itself, any work you do on it, your DigitalOcean account, your Anthropic Max subscription.
- **What we orchestrate**: initial provisioning (cloud-init, package install, tunnel setup), dashboard access, embedded browser terminal.

---

## 3. Payment

All payments are processed by Stripe, Inc. By completing a purchase you agree to Stripe's terms of service. We do not store your payment card details; Stripe handles all card data under PCI-DSS compliance.

The purchase price is **$99.00 USD**, charged once at the time of purchase. There are no recurring charges from Concerto. Your ongoing DigitalOcean Droplet costs are billed separately by DigitalOcean to your account.

---

## 4. Refund Policy

If your Droplet never reaches a "ready" state — meaning our provisioning process failed to successfully complete the installation — you are entitled to a **full refund** within **14 days** of your purchase date. To request a refund, email us at **support@concerto.run** with your purchase email address. We will process the refund through Stripe within 5 business days of approving your request.

Once provisioning has completed successfully (you can access your Droplet via the dashboard), refunds are not available. The Droplet has been created inside your DigitalOcean account and belongs to you; the service has been rendered.

A complete, standalone Refund Policy is available at [concerto.run/legal/refund](/legal/refund).

---

## 5. Your Responsibilities

**DigitalOcean account**: You are responsible for providing a valid DigitalOcean API key with write permissions. Your DigitalOcean bill (for the Droplet's compute time) is between you and DigitalOcean. We are not responsible for your DO charges.

**Anthropic Max subscription**: Claude Code requires an Anthropic Max subscription. Obtaining and maintaining that subscription is your responsibility.

**Lawful use**: You may not use Concerto to provision Droplets for any purpose that violates DigitalOcean's Acceptable Use Policy, Anthropic's usage policies, or applicable law. See our full [Acceptable Use Policy](/legal/aup) for specifics.

**Security**: Your dashboard token grants access to your Droplet's terminal. Treat it like a password. Do not share it publicly.

**Your data**: Anything you store on your Droplet or run through your Claude Code agents is your responsibility. We do not access, monitor, or retain your code, conversations, or outputs.

---

## 6. What We Provide and Do Not Guarantee

We will make reasonable efforts to provision your Droplet successfully and keep the Concerto dashboard operational. However, the service is provided **"as is"** without warranties of any kind, express or implied. We do not guarantee:

- Uninterrupted availability of the Concerto dashboard
- Compatibility with future versions of Claude Code, DigitalOcean's API, or Anthropic's services
- That your Droplet will remain reachable if DigitalOcean experiences an outage or you exhaust your DO billing

---

## 7. Limitation of Liability

To the maximum extent permitted by applicable law, our total liability to you for any claim arising from your use of Concerto — regardless of the legal theory — is limited to **the amount you paid us**, which is $99.00 USD. We are not liable for indirect, incidental, consequential, or punitive damages.

This limitation exists because the infrastructure is in your hands: you own the Droplet, you control the DigitalOcean account, and any material loss would occur in your own cloud environment, not in ours.

---

## 8. Termination

We reserve the right to suspend or terminate your Concerto dashboard access if:

- We detect abuse as described in our Acceptable Use Policy
- You initiate a fraudulent chargeback after a successful provisioning
- You take actions that materially harm our infrastructure or other users

Termination of dashboard access does not affect the Droplet in your DigitalOcean account — that remains yours.

---

## 9. Privacy

We take your privacy seriously. We collect the minimum data needed to deliver the service. See our full [Privacy Policy](/legal/privacy) for details on what we collect, how we store it, and your rights under GDPR.

---

## 10. Changes to These Terms

We may update these Terms by posting a new version at concerto.run/legal/terms with an updated "Last updated" date. Continued use of the service after changes are posted constitutes acceptance. We will make reasonable efforts to notify existing customers of material changes via email.

---

## 11. Governing Law

These Terms are governed by the laws of France, without regard to conflict-of-law principles. Any disputes that cannot be resolved amicably shall be subject to the exclusive jurisdiction of the courts of Paris.

---

## 12. Contact

**Email**: support@concerto.run

Questions about these terms? Email us — we're a small team and we respond to real questions.
