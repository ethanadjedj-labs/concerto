# Maestro Security

## Overview

Maestro's design principle: **your code and your conversations never touch our servers.** The Maestro backend is a thin provisioning layer. The compute, the Claude Code process, and all files live on a Droplet inside *your* DigitalOcean account.

---

## Bearer Tokens

- Every API call from the Maestro frontend to the Maestro backend is authenticated with a short-lived JWT signed with a server-side secret (HS256).
- Tokens are issued after Stripe confirms payment and are scoped to a single customer record.
- Tokens are never embedded in URLs, only in `Authorization: Bearer` headers.
- Token TTL: 24 h for setup flows, 7 d for dashboard access. Refresh is transparent via the frontend.

---

## DigitalOcean API Key Handling

1. **Collection**: The customer enters their DO Personal Access Token in the Maestro setup page over HTTPS.
2. **Transmission**: The key is sent to the Maestro backend over TLS 1.2+. It is never logged, never forwarded to third parties.
3. **Storage**: The key is encrypted with AES-256-GCM using a server-side master key (`DO_KEY_ENCRYPTION_KEY` env var, loaded from `/etc/maestro/env` on the backend host). The ciphertext is stored in SQLite alongside a per-record random nonce.
4. **Use**: The key is decrypted in memory only when needed to call the DO API (create Droplet, query status, or destroy on refund). The plaintext is never written to disk post-encryption.
5. **Deletion**: On customer request or automatic cleanup (see Data Retention), the row is deleted and the key is irrecoverable.

---

## cloud-init and the Installer

`cloud-init` runs the Maestro bash installer at first boot. It:

- Installs system packages (Node.js, Python, cloudflared, ttyd) from official repos.
- Creates a non-root user `maestro` and runs Claude Code under that user.
- Applies `ufw` rules: default deny inbound, allow outbound. **No SSH port is opened by default.**
- Sets up `cloudflared` as a systemd service with the customer's unique tunnel token (passed via user data field, which is write-once and not accessible after boot via the DO API by default).
- Starts the MCP relay server on `127.0.0.1` only.

The installer script is hosted at `install.maestro.run` and its SHA-256 is verified before execution.

---

## Why ttyd Is Tunnel-Only

ttyd provides the web terminal customers use for the one-time Claude OAuth. It is:

- Bound to `127.0.0.1:7681` — not reachable from the internet.
- Exposed only through the Cloudflare tunnel (which requires Cloudflare auth).
- Protected by a one-time session token issued by the Maestro backend during setup.
- Disabled after OAuth completes (systemd `oneshot` service).

After the OAuth step, ttyd is stopped. The tunnel remains open only for the MCP relay.

---

## SSH Key Handling

By default, **SSH is not enabled** on Maestro-provisioned Droplets. Customers who want SSH access can provide their own public key during setup. If provided:

- The key is injected via `cloud-init` into `/home/maestro/.ssh/authorized_keys`.
- The Maestro backend never stores or sees the private key (customers provide only the public key).
- `sshd` is enabled and port 22 is opened in `ufw` only if a key is provided.

---

## What the Backend Can and Cannot Access

| Action | Can the backend do it? |
|--------|------------------------|
| Create/destroy Droplets | Yes — uses the stored DO API key |
| Read Droplet status | Yes — uses the stored DO API key |
| SSH into the Droplet | No — we do not store SSH private keys |
| Read files on the Droplet | No — no access path after provisioning |
| Read Claude conversation content | No — conversations go directly claude.ai → tunnel → droplet; Maestro backend is not in that path |
| Read source code on the Droplet | No — same reason |
| Exfiltrate DO API key | Technically possible (it's stored encrypted); we mitigate via encryption + access controls + deletion on request |

---

## Data We Store

| Data | Purpose | Encryption |
|------|---------|------------|
| Customer email | Payment confirmation, transactional emails | Plaintext in SQLite (low sensitivity) |
| DO API key | Droplet provisioning | AES-256-GCM, server-side key |
| Droplet ID | Dashboard, destroy on refund | Plaintext in SQLite |
| Cloudflare tunnel ID | Tunnel management | Plaintext in SQLite |
| Stripe payment intent ID | Refund handling, audit | Plaintext in SQLite |

## Data We Do NOT Store

- Claude conversation content
- Source code, files, or artifacts on the Droplet
- Claude OAuth tokens (issued by Anthropic, stored on the Droplet only)
- SSH private keys

---

## GDPR Posture

Maestro stores a minimal set of personal data:

| Personal Data | Legal Basis | Retention |
|--------------|-------------|-----------|
| Email address | Contract performance | Duration of service + 90 days |
| DO API key | Contract performance | Deleted on Droplet destruction or explicit request |
| Payment metadata | Legal obligation (tax) | 7 years (Stripe retains full payment records) |

Customers may request deletion of all personal data by emailing **privacy@maestro.run**. Deletion is completed within 30 days. Note: Stripe payment records are retained by Stripe per their own GDPR compliance obligations and cannot be deleted by Maestro.

---

## Data Retention Policy

| Data | Retention Period |
|------|-----------------|
| Active customer records (email, DO key, droplet ID) | Until explicit deletion request or 90 days after last activity |
| Stripe webhook events | 90 days (soft delete) |
| System access logs | 30 days rolling |
| Email delivery logs | 30 days |

Destroyed Droplet records are purged from our SQLite within **7 days** of destruction. DO API keys for destroyed Droplets are zeroed immediately upon Droplet destruction.

---

## Responsible Disclosure

Found a security issue? Email **security@maestro.run** with details. We aim to respond within 48 hours. We do not have a formal bug bounty program yet, but we acknowledge researchers publicly if they wish.
