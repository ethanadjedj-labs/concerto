# Product Hunt — Listing Draft

> **Where Ethan posts this:** https://www.producthunt.com/posts/new — schedule for
> 12:01am PT on launch day (Tue or Wed best). Maker comment ready to post within
> 30 minutes of launch. Coordinate 10–15 genuine supporters to upvote and comment
> honestly — no incentivized upvotes (PH bans this). Monitor comments every 2h
> through noon PT.

---

## Name

> Concerto

## Tagline (60 chars max)

> Run multiple Claude Code sessions in parallel, from one chat

*[58 chars ✓]*

---

## Description (260 chars max)

> Concerto is an MCP server that lets a single Claude conversation orchestrate
> parallel Claude Code sessions on a managed VPS — spawn, monitor, kill from chat.
> Five tools, one URL into Claude Desktop or Code. Solo $49/mo, Pro $99/mo.

*[254 chars ✓]*

---

## First Comment — From the Maker (~110 words)

Hey Product Hunt 👋

I built Concerto for a problem I kept hitting with Claude Code: it's great at one
focused task and painful at three. The moment I wanted parallel work — refactor
here, bisect there, prototype on a branch — I was juggling terminals instead of
shipping.

Concerto exposes five MCP tools — start, list, get, kill, build — to any Claude
chat. Sessions run on a managed VPS so they survive your laptop sleeping. Your
chat becomes the orchestrator; you stop being the human MCP between three
terminals.

Solo $49/mo, Pro $99/mo. Bring your Claude Pro/Max. Would love feedback —
especially from people who already run Claude Code seriously.

*[~115 words — trim to taste]*

---

## Topics

> Developer Tools · Artificial Intelligence · Productivity · Open Source

## Links

- Website: https://concerto.run
- GitHub: https://github.com/ethanadjedj-labs/concerto
- MCP Registry: https://registry.modelcontextprotocol.io (search "concerto")
- Demo video: **[TO RECORD — 60-sec screen capture, see `docs/distribution/demo_script_90sec.md`]**

## Thumbnail

> **[NEEDED — 240×240 PNG, Concerto logo on cream background. Source files in
> `frontend/public/brand/`]**

## Gallery images (3 minimum)

1. Hero: "Run multiple Claude Code sessions from one Claude chat" — landing page screenshot.
2. The 5 MCP tools in Claude Desktop's connector pane.
3. A real chat where Claude calls `start_claude_session` twice and reports back when both finish.
4. Architecture diagram (optional 4th) from `docs/ARCHITECTURE.md`.

---

## Launch-day notes

- Schedule the post itself for 12:01am PT (PH treats your local time zone as your
  launch day; PT maximizes US daytime exposure).
- Maker comment must be posted within ~30 min of go-live or PH's algorithm
  deprioritizes the listing.
- Reply to every substantive comment same-day. The thread quality is itself a
  ranking signal.
- Do NOT incentivize upvotes (PH bans this and shadow-removes products that do it).
