# Terms of Service

**Concerto** — Hosted MCP Server for Claude Code Orchestration

_Last updated: 2026-06-04_

---

## 1. Who We Are and What Concerto Does

Concerto is a hosted MCP (Model Context Protocol) server operated by Ethan Adjedj ("we," "us," "our"). When you subscribe to Concerto, you receive a personal MCP endpoint that you connect to Claude using a single command:

```
claude mcp add --transport http concerto https://api.concerto.run/mcp-proxy/<your-token>/mcp
```

Your token appears in your dashboard immediately after checkout. The same command works for Claude Desktop and any other MCP-compatible client.

Concerto manages all infrastructure on its own servers. You do not provision, own, or pay for any third-party cloud account or virtual machine as part of this service.

---

## 2. The Service in Plain Terms

- **What you pay us**: a recurring subscription fee, charged monthly by Stripe (Solo — $49/mo, Pro — $99/mo). Free 30-minute trials are available without a card.
- **What you get**: a personal, hosted MCP server endpoint. Connect Claude to it and Claude can orchestrate Claude Code sessions on Concerto-managed infrastructure.
- **What remains yours**: your Claude conversations, your code, your Anthropic account.
- **What we manage**: the MCP server, Claude Code orchestration workers, uptime, and all underlying cloud infrastructure.

---

## 3. Payment

All payments are processed by Stripe, Inc. By completing a purchase you agree to Stripe's terms of service. We do not store your payment card details; Stripe handles all card data under PCI-DSS compliance.

Subscriptions are billed monthly at the rate shown at checkout. Stripe will charge your payment method automatically on each renewal date. You can cancel at any time from your dashboard or by emailing support@concerto.run.

---

## 4. Refund Policy

If the Concerto MCP service is not functional after purchase — meaning you cannot connect Claude using the provided command within 14 days of purchase — you are entitled to a **full refund**. Email **support@concerto.run** with your purchase email address. We will process approved refunds through Stripe within 5 business days.

Once you have successfully connected Claude to your Concerto endpoint and the service has been rendered, refunds are not available except at our discretion.

A complete, standalone Refund Policy is available at [concerto.run/legal/refund](/legal/refund).

---

## 5. Your Responsibilities

**Anthropic account**: Claude Code requires an Anthropic Max subscription. Obtaining and maintaining that subscription is your responsibility.

**Your dashboard token**: Your token authenticates your MCP connection. Treat it like a password. Do not share it publicly.

**Lawful use**: You may not use Concerto to run code or orchestrate tasks that violate Anthropic's usage policies or applicable law. See our full [Acceptable Use Policy](/legal/aup) for specifics.

**Your data**: Anything you run through your Claude Code sessions is your responsibility. We do not access, monitor, or retain your code or conversation outputs.

---

## 6. What We Provide and Do Not Guarantee

We will make reasonable efforts to keep the Concerto MCP service operational. However, the service is provided **"as is"** without warranties of any kind, express or implied. We do not guarantee:

- Uninterrupted availability of the MCP endpoint or orchestration workers
- Compatibility with future versions of Claude Code or Anthropic's services
- That service will remain available if Anthropic changes its API or policies in ways that affect our infrastructure

---

## 7. Limitation of Liability

To the maximum extent permitted by applicable law, our total liability to you for any claim arising from your use of Concerto — regardless of the legal theory — is limited to **the amount you paid us in the three months preceding the claim**. We are not liable for indirect, incidental, consequential, or punitive damages.

---

## 8. Termination

We reserve the right to suspend or terminate your Concerto access if:

- We detect abuse as described in our Acceptable Use Policy
- You initiate a fraudulent chargeback
- You take actions that materially harm our infrastructure or other users

Cancellation of your subscription takes effect at the end of your current billing period.

---

## 9. Privacy

We take your privacy seriously. We collect the minimum data needed to deliver the service. See our full [Privacy Policy](/legal/privacy) for details on what we collect, how we store it, and your rights under GDPR.

---

## 10. Changes to These Terms

We may update these Terms by posting a new version at concerto.run/legal/terms with an updated "Last updated" date. Continued use of the service after changes are posted constitutes acceptance. We will make reasonable efforts to notify existing subscribers of material changes via email.

---

## 11. Governing Law

These Terms are governed by the laws of France, without regard to conflict-of-law principles. Any disputes that cannot be resolved amicably shall be subject to the exclusive jurisdiction of the courts of Paris.

---

## 12. Contact

**Email**: support@concerto.run

Questions about these terms? Email us — we're a small team and we respond to real questions.
