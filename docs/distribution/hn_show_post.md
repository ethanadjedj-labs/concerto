# Show HN: Concerto

> **Where Ethan posts this:** https://news.ycombinator.com/submit — title in the
> "title" field, body below in the "text" field. URL field stays empty (Show HN
> with text body, not a link post). Post Tue–Thu 8:30am ET.

---

**Title** (HN limit: 80 chars):

> Show HN: Concerto – run multiple Claude Code sessions in parallel over MCP

*[75 chars ✓]*

---

**Body**:

I built Concerto because Claude Code is great at one task at a time and bad at
three. The moment I wanted to refactor in one repo, bisect a regression in another,
and prototype a feature on a third branch, I was back to juggling tmux panes,
copy-pasting logs into chat, and re-priming context every time I switched.

Concerto is an MCP server that exposes five tools to a Claude conversation:

- `start_claude_session(prompt, model)` – spawn a Claude Code agent
- `list_claude_sessions()` – what's running, what's done
- `get_claude_session(id)` – tail output, check progress
- `kill_claude_session(id)` – stop cleanly
- `concerto_build(request)` – high-level "plan + spawn" intent

Sessions run on a managed VPS, persist across laptop sleeps, and stream back
through tool returns. Your Claude chat becomes the orchestrator.

**Stack**: streamable-HTTP MCP, OAuth 2.1 + PKCE per-customer auth, sessions
live under tmux, FastAPI control plane, cloud-init bootstrap for the per-tenant
VPS. Code: ~1k LOC of MCP server + ~3k LOC of control plane. Connection is one
URL into Claude Desktop / Claude Code CLI / any MCP client.

**Pricing**: Solo $49/month (one managed VPS, parallel sessions). Pro $99/month
(bigger VPS, more concurrent sessions, priority email support). Bring your own
Claude Pro or Max subscription — Concerto provides the orchestration, Anthropic
does the inference.

**What I'm uncertain about**: how many people actually need three Claude Code
sessions running at once. My own use went from "occasionally" to "every day"
within a week of having the tool available, but I might be an outlier. Curious
how others think about the threshold where orchestration starts to matter.

concerto.run — feedback welcome, including the harsh kind.
