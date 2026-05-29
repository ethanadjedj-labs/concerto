<!-- layer: PRODUCT -->
# CLAUDE.md — concerto

**Layer:** PRODUCT | **Job:** MCP tool that orchestrates parallel Claude Code sessions (concerto.run); owns its own buyers, payments, and subscription lifecycle.

> Portfolio context: /opt/infra/docs/PORTFOLIO_GUIDE.md — read §1 (layer model) and §2 (hard rules) first.
> Fallback copy: /var/lib/empire/audits/ONBOARDING.md

---

# PART A — Universal rules (do not modify)

## A.1 ANTI-FREEZE (NON-NEGOCIABLE)

1. **No parallel subagents.** One agent / sub-agent at a time. Sequential only.
2. **Split large writes.** A single `Write` call > ~150 lines can freeze the harness.
3. **Commit after each step.** One logical change = one commit.
4. **Reports: synthesis > dump.** Actionable synthesis, not verbatim copy.
5. **`git push` regularly.** Every 3–4 steps minimum.
6. **Slow down ⇒ commit + push, then continue.**

## A.2 GIT

Branch: `claude/<slug>-<token>`. Conventional-commit prefix. No `push --force` to `main`.

---

# PART B — concerto-specific

## B.1 Identity

- **DB:** `/var/lib/concerto/concerto.db` — tables: `buyers`, `subscriptions`, `sessions`.
- **HTTP:** FastAPI backend; port in `/etc/empire/concerto.env`.
- Independently sellable/killable product. Has its own Stripe product and buyer table.
- Surfaces as an MCP server that end-users install; the backend manages session orchestration.

## B.2 Install + test

```bash
cd /opt/concerto
pip install -e .
python -m pytest -q
python -c "import backend; print('ok')"
```

## B.3 Hard constraints

- **This is NOT a VPS session template.** Don't use CLAUDE.md instructions here to write session-startup sqlite queries — that was the old wrong content.
- Uses `runtime` (via HTTP only) for session state and MCP bridge; never imports runtime internals.
- Payment logic stays in concerto's own `buyers` table + arsenal Stripe primitives. No cross-product buyer sharing.
- Email sends go through mailroom `POST /send` with `product=concerto`.
- Signal reads go through `arsenal.lake_client`, never direct `signals.db` file access.
