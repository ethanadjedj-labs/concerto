# Your first 5 minutes with Concerto

Welcome. Your Concerto VPS is running Claude Code connected to your claude.ai account. Here's how to get started.

## Step 1 — Send your first session

In any claude.ai conversation with the Concerto connector active, type:

> Spawn a Concerto session to write a hello world Python script.

Watch Claude use the MCP tools to start a session on your VPS. It will return a session ID.

## Step 2 — Check the session

> List my Concerto sessions.

Claude calls `list_claude_sessions` and shows you what's running.

## Step 3 — Pull the output

> What did the hello world session return?

Claude calls `get_claude_session` with the session ID and surfaces the result — including the JSON envelope if the session printed one.

## Step 4 — Do real work

Replace the hello world prompt with something useful for your actual work. A few examples:

- "Spawn a Concerto session to clone my GitHub repo and run the test suite."
- "Spawn a Concerto session to set up a Python Flask app in /opt/concerto-workspace/myapp/."
- "Spawn 3 parallel Concerto sessions: one to audit the backend, one to lint the frontend, one to check dependencies."

See `examples/parallel_workflow.md` for the parallel pattern.

## Step 5 — Edit MANAGER_STATE.md

Open `/opt/concerto-workspace/OPS/MANAGER_STATE.md` and write down what you're building, your active projects, and any standing decisions. Every future session reads this file first — it's how Concerto sessions stay coherent across conversations.

---

## File layout

```
/opt/concerto-workspace/
  OPS/
    MANAGER_STATE.md      ← ground truth — edit this
    SESSION_RULES.md      ← session conventions
    ENVELOPE_SCHEMA.md    ← return format for sessions
    queue/                ← optional: pending/done/failed prompt queue
  examples/
    sample_prompt.md      ← well-formed session prompt template
    parallel_workflow.md  ← how to run parallel sessions
  .claude/
    CLAUDE.md             ← Claude Code project instructions (auto-loaded)
```
