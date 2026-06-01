---
title: PR #7242 — exact response to glama-check bot
status: ready-for-ethan (post on PR after Glama listing is live)
last_reviewed: 2026-06-01
---

# PR #7242 — exact response to the `glama-check` bot

**PR:** https://github.com/punkpeye/awesome-mcp-servers/pull/7242
**Bot comment we're answering:** https://github.com/punkpeye/awesome-mcp-servers/pull/7242#issuecomment-4595567807

The `glama-check` action requires two things before the maintainers will merge:

1. A live Glama listing at `https://glama.ai/mcp/servers/<owner>/<repo>`
2. A Glama score badge embedded in the README entry on this PR

This file is the **exact comment + diff** Ethan posts to the PR once step 1 is live.

---

## Step 1 (do first, off-PR): list Concerto on Glama

Use the payload in [`glama.md`](glama.md). Once submitted, the URL pattern is
`https://glama.ai/mcp/servers/ethanadjedj-labs/concerto` (Glama derives the slug
from the GitHub `owner/repo`). The score badge becomes available at
`https://glama.ai/mcp/servers/ethanadjedj-labs/concerto/badges/score.svg`.

Wait until the badge image renders (Glama needs to finish indexing — usually
minutes, sometimes hours).

## Step 2: amend the PR's README line to embed the badge

Locally:

```bash
cd /tmp && rm -rf awesome-mcp-servers && \
git clone --branch add-concerto git@github.com:ethanadjedj/awesome-mcp-servers.git && \
cd awesome-mcp-servers
```

Open `README.md`, find the line under **🤖 Coding Agents**:

```markdown
- [ethanadjedj-labs/concerto](https://github.com/ethanadjedj-labs/concerto) 🐍 ☁️ - Orchestrate parallel Claude Code sessions over MCP. Hosted MCP server with `start_claude_session`, `list_claude_sessions`, `get_claude_session`, and `kill_claude_session` so any MCP client (Claude Desktop, Claude Code, Cursor, Zed, VS Code) can spawn, inspect, and kill long-running Claude Code agents on a managed VPS that survive between turns.
```

Replace with (badge inserted directly after the description, per the bot's example format):

```markdown
- [ethanadjedj-labs/concerto](https://github.com/ethanadjedj-labs/concerto) 🐍 ☁️ - Orchestrate parallel Claude Code sessions over MCP. Hosted MCP server with `start_claude_session`, `list_claude_sessions`, `get_claude_session`, and `kill_claude_session` so any MCP client (Claude Desktop, Claude Code, Cursor, Zed, VS Code) can spawn, inspect, and kill long-running Claude Code agents on a managed VPS that survive between turns. [![ethanadjedj-labs/concerto MCP server](https://glama.ai/mcp/servers/ethanadjedj-labs/concerto/badges/score.svg)](https://glama.ai/mcp/servers/ethanadjedj-labs/concerto)
```

Commit + push:

```bash
git add README.md
git commit -m "Add Glama score badge to Concerto entry (per glama-check bot)"
git push origin add-concerto
```

## Step 3: post the comment below on PR #7242

```
Thanks @glama-check — addressed both items:

1. Concerto is now listed on Glama: https://glama.ai/mcp/servers/ethanadjedj-labs/concerto
2. Glama score badge embedded in the README entry on this PR (latest commit on `add-concerto`).

For the maintainers — Concerto is a hosted remote MCP server (streamable-HTTP, OAuth 2.1), so its Glama entry uses the hosted-connector flow rather than a Dockerfile. Happy to clarify anything that helps review.
```

(Paste verbatim. The `@glama-check` mention pings the bot to re-run.)

---

## If the badge URL 404s after submission

Glama sometimes takes longer than expected to mint the score badge. If
`https://glama.ai/mcp/servers/ethanadjedj-labs/concerto/badges/score.svg` is
still 404 after ~24h:

- Check the Glama Discord (`https://glama.ai/discord`) per the bot comment.
- The bot also says hosted servers can additionally be listed under
  `https://glama.ai/mcp/connectors` — this is the right surface for Concerto's
  remote-streamable-http transport, and the badge lives at the same URL pattern.

## Why not just remove the badge requirement / argue with the bot

We *could* argue, but the maintainers run that bot deliberately to keep the list
free of broken servers — and the list is "synced with" Glama editorially, so a
parallel Glama listing is on the recovery path anyway. Cheaper to satisfy.
