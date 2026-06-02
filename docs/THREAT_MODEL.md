# Concerto Threat Model

_Last updated: 2026-06-02. Reviewed against `backend/concerto/*.py` at commit `6e2265a`._

This document enumerates the real adversary-facing attack surface of the
Concerto control plane (`api.concerto.run`) and per-buyer MCP proxy.  It is
written from the perspective of an attacker who can hit any public endpoint
and who has signed up for a trial buyer account themselves (so they own a
valid `token`, `bearer_token`, `ttyd_password`, `callback_secret`, and an
NF service URL they can reach).

Findings are ranked by `severity × exploitability`.  Each finding cites the
code path and explains the actual attack, not just the theoretical class.

## Scope

In scope:

  * Public HTTP surface: every route under `backend/concerto/*_router.py`
    plus `mcp_proxy_router.py` and `stripe_webhook.py`.
  * The buyer-`token` opaque-bearer model: `token` IS the only authenticator
    on every `/api/buyer/{token}/...` route.
  * Stripe webhook signature, idempotency, and event allow-listing.
  * GitHub-OAuth integration (`github_router.py`).
  * The trial-eligibility / abuse path.
  * The per-buyer MCP proxy at `/mcp-proxy/{buyer_token}/{path}`.
  * The "internal" callback endpoints (`/api/internal/*`) and their secrets.
  * The operator/admin endpoints (`/api/admin/*`, `/api/demand/*`).
  * Backend-host secret handling (env vars, log hygiene).

Out of scope (separately owned):

  * The Northflank account, the Cloudflare zone, the operator DigitalOcean
    org, the Stripe account itself.
  * The customer's Anthropic OAuth token after it is minted on the droplet.
  * Anything inside the customer's droplet/NF container (the customer owns
    that compute by design).

## Findings

### F-01 ─ CRITICAL ─ GitHub-OAuth state == buyer token → GitHub-token theft

**Code:**
  * `backend/concerto/github_router.py:107-115` (`/api/buyer/{token}/github/connect`)
  * `backend/concerto/github_router.py:388-409` (`/api/github/callback`)
  * `backend/concerto/github_router.py:447-473` (`/api/buyer/{token}/git-credentials`)

**Issue:**
The GitHub OAuth `state` parameter is the literal buyer `token`.  The
callback handler trusts whatever `state` GitHub echoes back and writes the
freshly-minted `access_token` onto `concerto_buyers WHERE token = <state>`
— no binding to the browser session that started the flow.

**Exploit:**
  1. Attacker signs up for a trial → owns `tok_attacker` and their own
     `callback_secret_attacker`.
  2. Attacker tricks the victim into clicking
     `https://github.com/login/oauth/authorize?client_id=…&state=tok_attacker&…`
     (this is just the URL `/api/buyer/tok_attacker/github/connect` redirects
     to; an attacker can host that link anywhere).
  3. Victim consents on github.com → GitHub posts the OAuth code to
     `https://api.concerto.run/api/github/callback?code=…&state=tok_attacker`.
  4. Backend exchanges the code for the **victim's** GitHub `access_token`
     and stores it on `tok_attacker`'s buyer row.
  5. Attacker calls
     `GET /api/buyer/tok_attacker/git-credentials -H "X-Callback-Secret: <attacker's own callback_secret>"`
     (this passes the `hmac.compare_digest` check trivially) and exfiltrates
     the victim's `github_token` — granting full `repo` scope on the
     victim's private repos.

The `tok_attacker` is the attacker's own buyer record, so they know its
`ttyd_password` and `callback_secret`; the `git-credentials` endpoint's
HMAC check is bypassed without any forgery.

**Fix:** Replace `state = <buyer_token>` with a server-minted, HMAC-signed,
short-TTL state that binds the flow to (a) a random nonce, (b) the
expected buyer token, and (c) an expiry.  Verify on callback before
trusting the buyer token.  Implemented as a stateless signed envelope so
no DB schema change is needed.  See `concerto.github_router._sign_state`.

---

### F-02 ─ CRITICAL ─ `droplet-ready` callback secret bypass when no secret stored

**Code:**
  * `backend/concerto/provision_router.py:238-307`

**Issue:**
The verification block is:

```python
stored_secret = buyer.get("callback_secret") or buyer.get("ttyd_password") or ""
if stored_secret and not hmac.compare_digest(stored_secret, incoming_secret):
    raise HTTPException(403, …)
```

When `stored_secret == ""` (the brand-new buyer row exists but the provisioner
has not yet stored either `callback_secret` or `ttyd_password`), the check is
**skipped entirely**.  An attacker who has any way to learn or guess a freshly
created buyer `token` during a ~30 s install window can POST `mcp_url=…` and
`bearer_token=…` of their choosing — pinning the buyer's MCP proxy to an
attacker-controlled host for the lifetime of that buyer (until the operator
notices and re-provisions).

For trial buyers, `token = secrets.token_urlsafe(32)` so blind enumeration is
infeasible — but anyone who can read access logs, cloudflare ray IDs, or
referer headers during install can supply that token.

**Exploit:**
  1. Attacker starts a trial → learns `token_self` and the install window
     opens.
  2. Race: attacker POSTs `/api/internal/droplet-ready` with their *own* token
     and `mcp_url = https://attacker.example/mcp`,
     `bearer_token = something`.  The check sees empty `stored_secret` and
     accepts the payload.
  3. When the legitimate provisioner later writes the real `mcp_url`, it may
     overwrite (race) or may not — but even if it does, the attacker has
     polluted the DB transiently and could re-race after every restart.

For *another* buyer's token (cross-tenant), the attacker also needs to know
the token, but **bypass = fail-open is the wrong default for any callback
secret check**.

**Fix:** Fail closed.  If no `stored_secret` is present, reject all callbacks
with 503 — the only legitimate caller (the provisioner setting `vps_id`)
writes `callback_secret` before any droplet can reach this endpoint.  The
provisioner already mints `callback_secret = secrets.token_hex(16)` and
writes it to the row, so the legitimate path is never affected.

---

### F-03 ─ HIGH ─ MCP proxy: path/host validation lets URL-shaped `path` reach unintended hosts

**Code:**
  * `backend/concerto/mcp_proxy_router.py:82-159`

**Issue:**
The forward target is built as `f"{vps_ip}/{path}"` with no scrub of `path`.

  * `path` is FastAPI's `{path:path}` capture and can contain `..`, `//`,
    NUL bytes, or even a fully-formed `https://…` after URL-decode.
  * `vps_ip` is whatever the DB has — which, by F-02, may be attacker-set on
    install race.  After F-02 is fixed, `vps_ip` is provisioner-written, so
    the practical concern reduces to `path`-traversal: an attacker could ask
    for `…/mcp-proxy/{tok}/..%2F..%2Fwhatever` to try to hit unintended
    internal endpoints on the NF container (e.g., the `__internal/*` admin
    surface).

**Exploit:**
A buyer constructs `GET /mcp-proxy/<their-own-token>/__internal/oauth/status`
and forwards through the public proxy — but they pass their *own* bearer,
because the proxy forwards the `Authorization` header.  This is the same
access they already have over the `vps_ip` URL directly.

So the actual risk surface is:
  1. Path-traversal probing for unexpected upstream endpoints (low — same
     ACL boundary as direct access);
  2. Future regression where some new upstream path is sensitive and the
     proxy provides a path-rewrite attack surface.

**Fix:** Validate `path` rejects `..`, NUL, scheme-like prefixes, and
unescaped double-slash; verify `vps_ip` is `https://…` with a known suffix.
Implemented as `_safe_target_url()` returning 400 on violation.

---

### F-04 ─ HIGH ─ Trial IP rate-limit trivially bypassable via `X-Forwarded-For`

**Code:**
  * `backend/concerto/trial_router.py:175-189`

```python
client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() \
    or request.client.host if request.client else "unknown"
```

**Issue:** The first hop in `X-Forwarded-For` is attacker-controlled.  A
script that sets `X-Forwarded-For: 1.1.1.1` then `…2.2.2.2` etc. can mint
unlimited trial buyers per email (still gated by email uniqueness in
`concerto_buyers`, but trivially defeated with disposable addresses).
Cost of abuse = N droplet provisions on the operator's DO account.

**Fix:** Prefer `cf-connecting-ip` (Cloudflare-set, attacker cannot forge
because Cloudflare strips/overwrites the customer-supplied header), fall
back to `request.client.host` (the L4 peer — also unforgeable).  Never
trust client-supplied `X-Forwarded-For`.

---

### F-05 ─ HIGH ─ Trial eligibility endpoint enumerates trial users by email

**Code:**
  * `backend/concerto/trial_router.py:212-229`

`GET /api/trial/eligibility?email=victim@example.com` returns
`{eligible: false, reason: "email_used"}` for any email that has ever
started a trial.  Useful for:

  * Confirming whether a target has tried Concerto (privacy / GDPR).
  * Enumerating customers in bulk against a known email list.

**Fix:** Return a uniform 204/200 response that does not reveal eligibility
based on the supplied email.  The legitimate caller (the trial-start form)
can check `_email_already_trialed` server-side at submit time and return
the same canonical "email already used" message — without exposing a probe
endpoint.

---

### F-06 ─ HIGH ─ Admin/ops endpoints use plain `==` token comparison

**Code:**
  * `backend/concerto/nf_admin_router.py:69`
  * `backend/concerto/demand_router.py:66`

```python
if not candidate or candidate != _OPS_TOKEN:
```

**Issue:** Python's `==` for strings is variable-time.  A network attacker
can in principle infer the prefix of `CONCERTO_OPS_TOKEN` byte by byte via
timing.  Practical risk is low over the public internet, but it is also a
trivial fix.

**Fix:** Use `hmac.compare_digest`.

---

### F-07 ─ MEDIUM ─ Ops token accepted in URL query string

**Code:**
  * `backend/concerto/nf_admin_router.py:58-71` and HTML page at `:523+`
  * `backend/concerto/demand_router.py:55-70`

Both admin surfaces accept `?token=<OPS_TOKEN>`.  The HTML dashboard page
even auto-strips the param from `location` after reading it.  Even so,
the token leaks into:
  * web-server access logs,
  * Cloudflare access logs,
  * browser history,
  * `Referer` headers to any cross-origin asset the page loads.

**Fix:** Continue to accept the query param for the HTML page (the only
ergonomic way to bookmark) but require the JSON `/api/admin/*` and
`/api/demand/*` endpoints to use the `Authorization: Bearer` header only.
That confines the leak risk to one HTML route and removes it from all
API surfaces that may be scraped or proxied.

---

### F-08 ─ MEDIUM ─ Cancel-link HMAC secret falls back to a per-process random

**Code:**
  * `backend/concerto/customer_portal.py:27`

```python
_CANCEL_LINK_SECRET = os.getenv("CONCERTO_CANCEL_LINK_SECRET") or secrets.token_hex(32)
```

If the env var is missing in prod, every restart silently invalidates every
outstanding cancel link (no observable error).  Worse, if two backend
replicas existed they would generate inconsistent secrets and outstanding
links would 50/50 break.

**Fix:** Require the env var when not in test mode; log a loud warning if
falling back.  (The fix may be a code change; rotating an existing secret
would be a SECURITY_BLOCKER item, but here the worst case is that we are
already using a per-process random — switching to a stable but
freshly-minted secret in env is purely additive.)

---

### F-09 ─ MEDIUM ─ CORS `allow_credentials=True` with wildcard methods/headers and env-supplied origins

**Code:**
  * `backend/concerto/server.py:63-72`

```python
_CORS_ORIGINS = ["https://concerto.run", "https://www.concerto.run"]
_extra = os.getenv("CONCERTO_EXTRA_ORIGINS", "")
if _extra:
    _CORS_ORIGINS.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(CORSMiddleware,
    allow_origins=_CORS_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])
```

The base allowlist is fine.  The risk: `CONCERTO_EXTRA_ORIGINS` accepts any
string, including `*` or a partially-rooted origin like `https://evil.com`.
A typo there reopens a cross-origin attack on every credentialed `/api/...`
route.

**Fix:** Validate each extra origin: must be `https://[host]` with no
wildcard, and refuse to start if any entry is malformed.  Bonus: keep
`allow_methods` to the explicit set actually used.

---

### F-10 ─ LOW ─ Webhook accepts and DB-records arbitrary unknown event types

**Code:**
  * `backend/concerto/stripe_webhook.py:329-590`

`_dispatch_event` falls through to a generic `{"received": True}` response
for any unrecognised event type, and `_mark_done` then writes it to
`stripe_processed_events`.  Stripe is signed so this is not a forgery
risk, but it grows the dedupe table unboundedly with events we never act
on (e.g. `customer.updated`, `invoice.created`, …).  Combined with
F-02-style cross-handler bugs, a future regression that *does* act on an
unexpected event type would not be caught.

**Fix:** Allow-list the event types we actually dispatch; for the rest,
return 200 immediately without claiming an idempotency row.  Defence in
depth.

---

### F-11 ─ LOW ─ Cancel-by-email rate-limits per L4 client IP behind Cloudflare

**Code:**
  * `backend/concerto/customer_portal.py:59-68`, `:185-190`

`request.client.host` behind Cloudflare returns a CF edge IP, so the per-IP
window is shared across many customers.  Either a CF IP rotation makes the
limit useless, or one noisy CF IP DoSes legitimate users.

**Fix:** Switch to `cf-connecting-ip` for keying (same pattern as F-04).
Also tighten the limit window — 3 attempts/hour/IP/email-pair is enough.

---

### F-12 ─ LOW ─ Buyer `token` is the sole authenticator for high-impact actions

**Code:**
  * `backend/concerto/customer_portal.py:80-110` (`/api/customer-portal-session`)
  * `backend/concerto/customer_portal.py:119-175` (`/api/cancel-subscription`)
  * `backend/concerto/status_router.py:64-87` (`/api/buyer/{token}/cancel`)

The buyer `token` is 128-bit (uuid4) or 256-bit (`secrets.token_urlsafe(32)`)
so guessing is infeasible.  But the token is shipped over email
(`https://concerto.run/dashboard/{token}`), shown in screenshots, present
in browser history, and routinely included in support emails.  Anyone who
sees it can cancel the subscription or jump to the Stripe billing portal.

This is **by-design** in Concerto's model and consistent with the
project's "frictionless link-only access" philosophy.  Documented here so
future code does not add even more destructive operations behind only
this token.  Not fixed in this pass.

---

## Out-of-Scope-but-Noted

  * **No bug-bounty program.**  `security@concerto.run` is the disclosure
    channel.  Acknowledged but unchanged.
  * **DO API key encryption claim in docs/SECURITY.md does not match
    `db.py`.**  Current BYOC code does NOT persist the customer DO API key
    at all — it is used in-flight from the request and discarded.  The
    `SECURITY.md` AES-256-GCM claim is therefore aspirational, not
    implemented.  This is a documentation correctness issue more than a
    security one (no key to leak), but should be reconciled.
  * **`ttyd_password` is reused as both a basic-auth credential to the
    upstream ttyd AND a callback secret** (legacy rows).  Migration 018
    introduced `callback_secret` to separate concerns; new buyers split
    them.  Legacy rows still conflate.  Not fixed here.

## What we are doing about it

Phase 2 in this same change adds failing security tests under
`backend/tests/security/` that demonstrate F-01, F-02, F-03, F-04, F-05,
F-06, and F-09 against the live code.  Phase 3 patches each finding and
makes the tests pass.  See the `SECURITY_HARDENING_2026-06-02` block
in `MEMORY.md` / git history.
