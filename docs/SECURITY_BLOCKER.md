# SECURITY_BLOCKER — operator action items

Items here require credentials only the operator (Ethan) controls.  The
backend code has already been hardened in the same change; these steps
finish the rollout.

---

## 1. Mint and persist `CONCERTO_GH_STATE_SECRET` in the backend env

**Why:** Phase 3 of the red-team work (commit `252a30f`) replaced the raw
`state = <buyer-token>` parameter in GitHub OAuth with an HMAC-signed
envelope (`concerto.github_router._sign_state`).  The signing key is
read from `CONCERTO_GH_STATE_SECRET`.  If that env var is missing, the
process falls back to a per-restart random — outstanding GitHub OAuth
flows will silently break on every backend restart.  The fallback also
logs:

    CONCERTO_GH_STATE_SECRET is not set; using per-process random.

If you see that warning in journalctl, this item is blocking the
GitHub-connect feature.

**Numbered steps:**

  1. On the backend host, generate a long random secret:

         openssl rand -hex 32

     (or `python3 -c 'import secrets; print(secrets.token_hex(32))'`).

  2. Append the line to `/etc/concerto/env` (or wherever the systemd
     unit's `EnvironmentFile=` points):

         CONCERTO_GH_STATE_SECRET=<paste-from-step-1>

  3. Restart the backend:

         systemctl restart concerto-backend

  4. Verify in the logs that the warning above is gone:

         journalctl -u concerto-backend -n 100 --no-pager | \
           grep CONCERTO_GH_STATE_SECRET

     Expected: no match.

  5. Smoke-test: from the dashboard, click "Connect GitHub", complete
     consent, confirm the callback succeeds.  (No DB migration is
     needed — the envelope is stateless.)

**Rotation:** This secret CAN be rotated by repeating the steps with a
fresh value.  Cost of rotation: any GitHub OAuth flow in progress at
that moment will fail (user clicks "Connect" again — no permanent
damage).  Do NOT roll back to an older value once a new one is live.

---

## 2. (Optional) Mint `CONCERTO_CANCEL_LINK_SECRET` for the cancel-by-email flow

**Why:** Same family of issue (per-restart random fallback) for the
cancel-by-email HMAC in `concerto.customer_portal`.  Not exploitable —
worst case is outstanding cancel links from before a restart silently
fail.  Listed here because the fix is identical and cheap.

**Numbered steps:** as above, with env var name
`CONCERTO_CANCEL_LINK_SECRET`.

---

## 3. (Audit) Confirm `CONCERTO_EXTRA_ORIGINS` is empty or strict

**Why:** F-09 hardening (commit `252a30f`) now refuses to start if
`CONCERTO_EXTRA_ORIGINS` contains a wildcard, http://, or any path
component.  This is a fail-loud guard, not a permission grant — but if
the env var was previously set to something the new validator
rejects, the backend will crash on next start.

**Numbered steps:**

  1. Check the current value on the backend host:

         grep CONCERTO_EXTRA_ORIGINS /etc/concerto/env || \
           echo "not set — safe"

  2. If set, confirm every comma-separated entry matches the pattern
     `https://<host>` with no trailing slash, no path, no `*`.

  3. If any entry fails the check, either remove it or normalise it
     to `https://<host>` form before the next `systemctl restart
     concerto-backend`.

---

## 4. (Reconcile) `docs/SECURITY.md` claim vs reality re: DO API key encryption

**Why:** `docs/SECURITY.md` currently states customer DigitalOcean
API keys are AES-256-GCM-encrypted in SQLite.  The current code
(`backend/concerto/db.py`, `backend/concerto/provision_router.py`)
does NOT persist BYOC customer DO keys at all — they are used in
flight from the request body and discarded.  This is a
documentation correctness problem, not a key-handling
vulnerability (no key is at rest to leak).

**Numbered steps:**

  1. Decide which statement is the source of truth: either remove
     the encryption claim from `docs/SECURITY.md`, or (if the
     intent is to encrypt-and-persist) open a follow-up to add
     `do_api_key_ciphertext` + `do_api_key_nonce` columns and the
     encrypt/decrypt helpers gated by a `DO_KEY_ENCRYPTION_KEY` env
     var per the doc.

  2. This is a docs-only fix from the security posture point of
     view — no rotation needed.

---

_Last updated 2026-06-02 by the Concerto red-team-then-harden goal._
