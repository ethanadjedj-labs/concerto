# Concerto — MCP Ecosystem Distribution

The single source of truth for every place Concerto is (or should be) listed across the MCP ecosystem, what its status is, and the exact next step.

Canonical metadata for every listing is `server.json` at the repo root, conforming to the Official MCP Registry schema (`https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`).

**Status legend**
- **LIVE** — listing is publicly reachable; link to it.
- **PR-OPEN** — submission filed; link to the issue/PR.
- **READY-FOR-ETHAN** — payload fully prepared; the one human action required is documented below.
- **BLOCKED** — needs upstream change before submission can proceed.

| # | Channel | Status | Evidence / next step |
|---|---|---|---|
| 1 | Official MCP Registry (`registry.modelcontextprotocol.io`) | READY-FOR-ETHAN | `server.json` validated locally. Ethan runs the publish command below (needs GitHub OAuth device code). |
| 2 | GitHub MCP Registry (`github.com/mcp`) | AUTO (downstream of #1) | Auto-ingested from the Official MCP Registry. No separate action. |
| 3 | PulseMCP (`pulsemcp.com/servers`) | AUTO (downstream of #1) | Auto-ingested weekly from the Official MCP Registry. Editorial newsletter feature is request-not-required. |
| 4 | Smithery (`smithery.ai`) | READY-FOR-ETHAN | URL-hosted submission via the Smithery dashboard or CLI. Payload below. |
| 5 | Glama (`glama.ai/mcp/servers`) | READY-FOR-ETHAN | Submit repo URL via Add Server. Payload below. |
| 6 | mcp.so (`mcp.so`) | READY-FOR-ETHAN | Open a submission issue on `chatmcp/mcp-directory`. Payload below. |
| 7 | `punkpeye/awesome-mcp-servers` | **PR-OPEN** | [PR #7242](https://github.com/punkpeye/awesome-mcp-servers/pull/7242) opened 2026-06-01 with the agent fast-track marker (`🤖🤖🤖` per CONTRIBUTING.md). One-line entry added in the 🤖 Coding Agents section between `elhamid/llm-council` and `freema/openclaw-mcp`. |

CI workflow `.github/workflows/mcp-publish.yml` re-publishes to the Official MCP Registry on every GitHub release tag, so listings cannot go stale.

---

## 1) Official MCP Registry — `registry.modelcontextprotocol.io`

**Source:** https://modelcontextprotocol.io/registry/quickstart and https://github.com/modelcontextprotocol/registry

**Status:** READY-FOR-ETHAN. The publish step needs Ethan's GitHub identity (device-code OAuth) — an autonomous agent cannot complete that.

**Exact steps (Ethan):**

```bash
# 1. Install the publisher CLI (one-time)
brew install mcp-publisher          # or download release: github.com/modelcontextprotocol/registry/releases

# 2. From /opt/concerto on his laptop or a workstation logged into GitHub
cd /opt/concerto

# 3. Authenticate (device-code OAuth — opens browser)
mcp-publisher login github

# 4. Publish (server.json already in repo root)
mcp-publisher publish
```

**Gotchas confirmed by spec:**
- Server name MUST start with `io.github.<github-owner>/` when using GitHub auth. Our `server.json` uses `io.github.ethanadjedj-labs/concerto`, matching the actual GitHub org.
- The registry is still labeled "preview" — schema may shift. CI auto-republishes on releases (see below).

---

## 2) GitHub MCP Registry — `github.com/mcp`

**Source:** https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/ and https://github.com/mcp

**Status:** AUTO-INGESTED from the Official MCP Registry. No separate submission. Concerto appears here automatically once step 1 succeeds.

The curated "partner tier" (Microsoft / GitHub / Dynatrace / …) is editorial; OSS servers appear in the broader registry view automatically.

---

## 3) PulseMCP — `pulsemcp.com/servers`

**Source:** https://www.pulsemcp.com/servers, https://www.pulsemcp.com/newsletter (newsletter rebranded to "The Agentic Loop", bi-weekly).

**Status:** AUTO-INGESTED weekly from the Official MCP Registry. Listing appears within ~7 days of step 1.

**For newsletter feature:** Ethan emails PulseMCP after a launch milestone (Show HN, Product Hunt) — there is no "request a feature" form, it's editorial. Don't submit before launch; have a clear traction artifact to point at.

---

## 4) Smithery — `smithery.ai`

**Source:** https://smithery.ai/docs/build/publish

**Status:** READY-FOR-ETHAN.

**Exact steps (Ethan):**

Option A — URL submission (recommended, no container build needed):
1. Go to https://smithery.ai/new
2. Paste the public MCP URL template: `https://api.concerto.run/mcp-proxy/{buyer_token}/mcp`
3. Smithery's wizard will detect the streamable-http transport and ingest the OpenAPI/tool metadata via the standard MCP `tools/list` call.

Option B — CLI:
```bash
smithery mcp publish "https://api.concerto.run/mcp-proxy/<a-test-buyer-token>/mcp" -n @ethanadjedj-labs/concerto
```

**Notes:**
- Concerto is a per-customer remote server (each buyer gets a unique URL token), so STDIO bundles and `smithery.yaml` are not applicable.
- The Smithery listing description and CTA copy live in `docs/listings/smithery.md` — copy-paste from there.

---

## 5) Glama — `glama.ai/mcp/servers`

**Source:** https://glama.ai/mcp/servers (and the indexer's repo-validation rules at https://glama.ai/mcp).

**Status:** READY-FOR-ETHAN.

**Exact steps (Ethan):**
1. Go to https://glama.ai/mcp/servers
2. Click "Add Server"
3. Paste GitHub repo URL: `https://github.com/ethanadjedj-labs/concerto`
4. Glama auto-indexes the README, schemas, Docker buildability, and release tags.

**Validation prerequisites we have already satisfied:**
- README contains an install snippet (root `README.md` updated by this distribution work).
- Repo has release tags (1.0.0 stamped in `installer/cloud_init.yaml.j2`; CI will publish a GitHub Release on tag).
- `server.json` at root is canonical metadata Glama can also use.

---

## 6) mcp.so — `mcp.so`

**Source:** https://mcp.so and https://github.com/chatmcp/mcp-directory.

**Status:** READY-FOR-ETHAN — listing is editorial; file a GitHub issue.

**Exact steps (Ethan):**

Open a new issue at https://github.com/chatmcp/mcp-directory/issues/new with:

- **Title:** `Add Concerto — orchestrate parallel Claude Code sessions`
- **Body:** copy from `docs/listings/mcp_so.md`.

Listings appear after the maintainer batches and merges them (typically days, not weeks).

---

## 7) `punkpeye/awesome-mcp-servers`

**Source:** https://github.com/punkpeye/awesome-mcp-servers, https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md.

**Status:** **PR-OPEN** — [PR #7242](https://github.com/punkpeye/awesome-mcp-servers/pull/7242), filed 2026-06-01.

**Submission details (for the record):**

- Fork: https://github.com/ethanadjedj/awesome-mcp-servers (branch `add-concerto`)
- PR title: `Add Concerto — parallel Claude Code orchestration over MCP 🤖🤖🤖`
- PR head: `ethanadjedj:add-concerto` → `punkpeye:main`
- One-line README edit, inserted alphabetically in the **🤖 Coding Agents** section between `elhamid/llm-council` and `freema/openclaw-mcp`.

**Entry added:**

```
- [ethanadjedj-labs/concerto](https://github.com/ethanadjedj-labs/concerto) 🐍 ☁️ - Orchestrate parallel Claude Code sessions over MCP. Hosted MCP server with `start_claude_session`, `list_claude_sessions`, `get_claude_session`, and `kill_claude_session` so any MCP client (Claude Desktop, Claude Code, Cursor, Zed, VS Code) can spawn, inspect, and kill long-running Claude Code agents on a managed VPS that survive between turns.
```

**Note on Glama prerequisite (now confirmed wrong):** Earlier guidance circulating online claimed that a Glama listing is a hard prerequisite for PRs to this awesome list. **The CONTRIBUTING.md does NOT enforce that** — and the maintainers explicitly opt agent-submitted PRs into a fast-track lane when the title carries `🤖🤖🤖`. The README is "synced with" Glama, so a parallel Glama listing helps discoverability, but it's not a gate.

**If the maintainer asks for changes:** comments will appear at the PR URL above. Pull `ethanadjedj:add-concerto` locally to amend.

---

## CI re-registration (anti-stale)

Workflow at `.github/workflows/mcp-publish.yml`:

- Trigger: `release: types: [published]` and `workflow_dispatch`.
- Steps: download `mcp-publisher`, run `mcp-publisher publish` with a GitHub Actions OIDC-issued token.
- Result: every Concerto release auto-bumps the Official MCP Registry entry, which propagates to GitHub MCP Registry and PulseMCP on their next ingest cycle.

This is the anti-stale guarantee: `server.json` is the only place version metadata lives, and it republishes itself.

---

## Related outreach assets

- [`docs/SEO_PAGES_LIVE.md`](SEO_PAGES_LIVE.md) — three buyer-intent keyword pages now live on `concerto.run/learn/...` (prerendered + in sitemap).
- [`docs/outreach/creators_top10.md`](outreach/creators_top10.md) — top 10 AI-coding YouTubers + X accounts with per-creator hooks.
- [`docs/outreach/newsletters_top.md`](outreach/newsletters_top.md) — newsletter shortlist (PulseMCP, Latent Space, Pragmatic Engineer, TLDR AI, Ben's Bites, AI Tidbits, The Rundown) with per-outlet hooks. PulseMCP feature pitch should fire immediately after registry submission #1 above lands.
- [`docs/distribution/hn_show_post.md`](distribution/hn_show_post.md), [`docs/distribution/producthunt_listing_draft.md`](distribution/producthunt_listing_draft.md), [`docs/distribution/twitter_launch_thread.md`](distribution/twitter_launch_thread.md), [`docs/distribution/twitter_thread_strandedgrid.md`](distribution/twitter_thread_strandedgrid.md) — ready-to-fire launch kits (none posted by the agent).

---

## Sources (verified 2026-06-01)

- [MCP Registry Quickstart](https://modelcontextprotocol.io/registry/quickstart)
- [modelcontextprotocol/registry on GitHub](https://github.com/modelcontextprotocol/registry)
- [Generic server.json reference](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md)
- [GitHub MCP Registry announcement](https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/)
- [Smithery — Publishing](https://smithery.ai/docs/build/publish)
- [Glama MCP servers directory](https://glama.ai/mcp/servers)
- [chatmcp/mcp-directory (mcp.so backing repo)](https://github.com/chatmcp/mcp-directory)
- [punkpeye/awesome-mcp-servers CONTRIBUTING](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md)
- [PulseMCP — server directory](https://www.pulsemcp.com/servers)
