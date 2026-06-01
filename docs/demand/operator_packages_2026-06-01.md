# Concerto Demand Radar — operator packages (top 5)

Each package is **a draft for the operator to review**. The system never auto-posts. Edit the disclosure, personalize the hook, then post AS yourself.

## 1. [hn] Ask HN: Who wants to be hired? (May 2026)
- **url:** https://news.ycombinator.com/item?id=48066702
- **author:** robertgardunia  (comment)
- **score:** 0.88  — angle: `orchestration`
- **why relevant:** core: agent-orchestration, multi-agent, mcp-orchestration | intent: explicit-question, looking-for-tool | freshness: 0.18
- **signals:** agent-orchestration, multi-agent, mcp-orchestration, explicit-question, looking-for-tool, show-me-how

**Draft reply** (edit before posting):

```
Hey — disclosure first: I'm the maker of Concerto (concerto.run), so take this with that grain of salt.

For multi-agent orchestration with Claude Code specifically, the gap I
kept hitting was: orchestrators that *spawn* agents are easy, but ones
that let the *parent conversation* spawn, inspect, and kill child
sessions through real tool calls (not text scraping) are rare.

Concerto is the hosted MCP server I built for exactly this — you talk to Claude (Desktop / Code / any MCP client), and Claude spawns, monitors, and kills N Claude Code sessions on a managed VPS. Sessions persist between chats and devices. $49/mo Solo, $99/mo Pro.
It exposes spawn/list/get_progress/kill as MCP tools, so a Claude in
Desktop or Code can drive a fleet without you ever touching tmux.

[Personalize: connect to "Location: Gig Harbor, WA, USA<p>Remote: Yes<p>Willing to relocate: Open to Bay Area for the right role; remote preferred otherwise<p>Technol…"; offer a hands-on if useful.]
```

## 2. [hn] Ask HN: What are you working on? (February 2026)
- **url:** https://news.ycombinator.com/item?id=46939513
- **author:** nlowell  (comment)
- **score:** 0.86  — angle: `parallel`
- **why relevant:** core: multiple-claude-code, claude-code-parallel | intent: explicit-question, looking-for-tool | freshness: 0.10
- **signals:** multiple-claude-code, claude-code-parallel, explicit-question, looking-for-tool, recommendation-ask

**Draft reply** (edit before posting):

```
Hey — disclosure first: I'm the maker of Concerto (concerto.run), so take this with that grain of salt.

The thing that actually breaks at N>1 Claude Code sessions is not
running them — `claude` can run N times — it's:
  - re-priming context every time you restart
  - tail/-f-ing N terminals to see which one needs your input
  - losing state when your laptop sleeps mid-refactor

Concerto is the hosted MCP server I built for exactly this — you talk to Claude (Desktop / Code / any MCP client), and Claude spawns, monitors, and kills N Claude Code sessions on a managed VPS. Sessions persist between chats and devices. $49/mo Solo, $99/mo Pro.
You talk to one Claude and ask it to "spawn 3 sessions: one on the
refactor branch, one on the bug, one on the perf spike." It reports
back, and the sessions survive disconnects.

[Personalize: reference "I'm thinking all the time about what the "best" way of using local AI agents like Claude &#x2F; Codex &#x2F; Gemini is. I'm trying to figure…" and offer to share the specific
config / a free trial if it fits.]
```

## 3. [hn] Show HN: AgentOS – Self-hosted web UI for managing multiple Claude Code sessions
- **url:** https://github.com/saadnvd1/agent-os
- **author:** saadn92  (2 points, 5 comments, story)
- **score:** 0.82  — angle: `parallel`
- **why relevant:** core: multiple-claude-code, claude-code-managed, juggling-terminals | intent: pain-statement, show-me-how | freshness: 0.10
- **signals:** multiple-claude-code, claude-code-managed, juggling-terminals, pain-statement, show-me-how

**Draft reply** (edit before posting):

```
Hey — disclosure first: I'm the maker of Concerto (concerto.run), so take this with that grain of salt.

The thing that actually breaks at N>1 Claude Code sessions is not
running them — `claude` can run N times — it's:
  - re-priming context every time you restart
  - tail/-f-ing N terminals to see which one needs your input
  - losing state when your laptop sleeps mid-refactor

Concerto is the hosted MCP server I built for exactly this — you talk to Claude (Desktop / Code / any MCP client), and Claude spawns, monitors, and kills N Claude Code sessions on a managed VPS. Sessions persist between chats and devices. $49/mo Solo, $99/mo Pro.
You talk to one Claude and ask it to "spawn 3 sessions: one on the
refactor branch, one on the bug, one on the perf spike." It reports
back, and the sessions survive disconnects.

[Personalize: reference "Hi all,<p>I just open-sourced AgentOS, a tool I built for myself when I got tired of juggling a bunch of terminal windows while working with…" and offer to share the specific
config / a free trial if it fits.]
```

## 4. [hn] We are building an open-source agentic company OS
- **url:** https://news.ycombinator.com/item?id=48020416
- **author:** tarasyarema  (comment)
- **score:** 0.81  — angle: `orchestration`
- **why relevant:** core: claude-code-orchestration, multi-agent | intent: how-do-i, recommendation-ask | freshness: 0.14
- **signals:** claude-code-orchestration, multi-agent, how-do-i, recommendation-ask, show-me-how

**Draft reply** (edit before posting):

```
Hey — disclosure first: I'm the maker of Concerto (concerto.run), so take this with that grain of salt.

For multi-agent orchestration with Claude Code specifically, the gap I
kept hitting was: orchestrators that *spawn* agents are easy, but ones
that let the *parent conversation* spawn, inspect, and kill child
sessions through real tool calls (not text scraping) are rare.

Concerto is the hosted MCP server I built for exactly this — you talk to Claude (Desktop / Code / any MCP client), and Claude spawns, monitors, and kills N Claude Code sessions on a managed VPS. Sessions persist between chats and devices. $49/mo Solo, $99/mo Pro.
It exposes spawn/list/get_progress/kill as MCP tools, so a Claude in
Desktop or Code can drive a fleet without you ever touching tmux.

[Personalize: connect to "Hi there!<p>For a while we've seen companies focused solely on the coding agent part, and specially building harnesses. We thought it would…"; offer a hands-on if useful.]
```

## 5. [hn] Show HN: Omar – A TUI for managing 100 coding agents
- **url:** https://omar.tech
- **author:** karim7  (17 points, 2 comments, story)
- **score:** 0.79  — angle: `parallel`
- **why relevant:** core: multiple-claude-code, multi-agent, juggling-terminals | intent: explicit-question, pain-statement | freshness: 0.11
- **signals:** multiple-claude-code, multi-agent, juggling-terminals, explicit-question, pain-statement

**Draft reply** (edit before posting):

```
Hey — disclosure first: I'm the maker of Concerto (concerto.run), so take this with that grain of salt.

The thing that actually breaks at N>1 Claude Code sessions is not
running them — `claude` can run N times — it's:
  - re-priming context every time you restart
  - tail/-f-ing N terminals to see which one needs your input
  - losing state when your laptop sleeps mid-refactor

Concerto is the hosted MCP server I built for exactly this — you talk to Claude (Desktop / Code / any MCP client), and Claude spawns, monitors, and kills N Claude Code sessions on a managed VPS. Sessions persist between chats and devices. $49/mo Solo, $99/mo Pro.
You talk to one Claude and ask it to "spawn 3 sessions: one on the
refactor branch, one on the bug, one on the perf spike." It reports
back, and the sessions survive disconnects.

[Personalize: reference "We were both genuinely impressed by Claude Code after it helped each of us fix nasty CI problems overnight. Doing those fixes manually would…" and offer to share the specific
config / a free trial if it fits.]
```

