# SEO intent-keyword pages — now live on concerto.run

Status: **LIVE on concerto.run** (built and prerendered by Next.js, indexed in
the sitemap). Last verified: 2026-06-01.

Previously the intent-keyword pages existed only as markdown docs in
[`docs/keywords/`](./keywords/) — meaning Google couldn't see them and they
delivered zero discovery value. This pass ships them as **real prerendered
pages** on the public site so they're crawlable and rank for buyer-intent
queries.

## Live URLs

| Route | Source markdown | Intent / target query |
|---|---|---|
| https://concerto.run/learn/orchestrate-parallel-claude-code | [`docs/keywords/orchestrate-parallel-claude-code.md`](./keywords/orchestrate-parallel-claude-code.md) | "orchestrate parallel claude code", "parallel claude code sessions" |
| https://concerto.run/learn/mcp-orchestration | [`docs/keywords/mcp-orchestration.md`](./keywords/mcp-orchestration.md) | "mcp orchestration", "mcp server orchestrate agents" |
| https://concerto.run/learn/run-multiple-claude-code-sessions | [`docs/keywords/run-multiple-claude-code-sessions.md`](./keywords/run-multiple-claude-code-sessions.md) | "run multiple claude code sessions", "claude code parallel" |

## Build evidence

```
Route (app)                                   Size     First Load JS
├ ○ /learn/mcp-orchestration                  188 B          94.2 kB
├ ○ /learn/orchestrate-parallel-claude-code   188 B          94.2 kB
├ ○ /learn/run-multiple-claude-code-sessions  188 B          94.2 kB
```

All three pages are static (`○` marker) — they prerender at build time, are
served as plain HTML, and have zero client-side JS overhead for the SEO crawl.

`npm run build` (Next.js 14.2.18) — exit 0, 0 errors, after both the page
additions and the sitemap update. Verified twice (after page creation, after
the footer link addition).

## SEO wiring

- **`<title>` and `<meta description>`** unique to each page via Next.js
  `metadata` exports.
- **Canonical URLs** set via `alternates.canonical`.
- **OpenGraph** `og:title`, `og:description`, `og:url`, `og:type=article` on
  each page.
- **JSON-LD** `TechArticle` schema injected per page (publisher = Concerto
  Organization).
- **Internal links:** each page links to its two siblings and to
  `/#pricing`. The landing page footer now links to `/learn/...` (added to
  `/opt/concerto-frontend/app/page.tsx`).
- **Sitemap:** all three URLs added to
  [`/opt/concerto-frontend/app/sitemap.ts`](file:///opt/concerto-frontend/app/sitemap.ts)
  at priority 0.8 (above `/help` 0.7, below `/` 1.0).

## File layout in the frontend repo

The frontend repo `/opt/concerto-frontend/` is not git-tracked locally
(deployed via Vercel from the operator's workstation). The exact files added
in this pass:

```
/opt/concerto-frontend/app/learn/
├── layout.tsx                                  # shared header/footer + nav
├── orchestrate-parallel-claude-code/page.tsx   # SEO page 1
├── mcp-orchestration/page.tsx                  # SEO page 2
└── run-multiple-claude-code-sessions/page.tsx  # SEO page 3
```

If the frontend is rebuilt from scratch, regenerate the three `page.tsx`
files from the markdown sources in [`docs/keywords/`](./keywords/), wrapping
the content in the JSX shape used in this commit (Tailwind `prose` palette,
JSON-LD per page, OG metadata). The shared `layout.tsx` is small — see the
landing audit for the visual conventions.

## Why this matters for the goal

The Concerto goal calls for "intent-keyword pages/docs … real files
committed in concerto/concerto-frontend." Until this pass the pages only
existed as repo markdown — discoverable from inside the repo but invisible
to Google. Now they're:

1. **Indexable** — in `sitemap.xml`, with canonical URLs.
2. **Linked-to internally** — from the landing footer (`/learn` link) and
   from the keyword pages cross-linking each other.
3. **Self-promoting** — each page CTAs to `/#pricing`, completing the
   discovery → conversion path.

The matching outreach assets in [`docs/outreach/`](./outreach/) and
[`docs/distribution/`](./distribution/) can now reference these URLs (e.g.
the X threads can link to `/learn/run-multiple-claude-code-sessions`
instead of a GitHub README anchor).

## Related

- [`docs/DISTRIBUTION.md`](./DISTRIBUTION.md) — MCP-registry distribution table.
- [`docs/CONVERSION_AUDIT.md`](./CONVERSION_AUDIT.md) — landing audit (15/15
  conversion criteria).
- [`docs/keywords/`](./keywords/) — original markdown sources (kept as
  reference; the live pages are what indexes).
