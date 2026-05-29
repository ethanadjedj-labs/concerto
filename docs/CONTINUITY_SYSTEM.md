# Concerto MCP Server — Continuity System

**Written:** 2026-05-23 (post-crash audit session)  
**Last modified:** 2026-05-23 (continuity-activation session)  
**File documented:** `/opt/concerto/installer/mcp_server.py`

---

## Status: ACTIVATED (pending Docker rebuild)

All 5 continuity activations are implemented in `installer/mcp_server.py`.
36 tests pass in `backend/tests/test_continuity.py`.
Changes are code-level only; they ship when Ethan triggers the Docker rebuild
per `REBUILD_PLAN_2026_05_23.md`.

---

## Activations (all implemented as of 2026-05-23)

### 1. State-aware `concerto_build` / planner

`concerto_build` reads `MANAGER_STATE_PATH` before calling `_run_planner`:

```python
state_content = _read_manager_state()
sections = _extract_state_sections(state_content)
active_projects = sections.get("Active projects", "")
pending_decisions = sections.get("Pending operator decisions", "")
```

- Extracts "Active projects" and "Pending operator decisions" sections
- Injects them as `## Workspace context (from MANAGER_STATE)` prefix in the
  planner prompt via `_run_planner(request, state_context)`
- Returns `context_used` debug field in the tool response (not user-facing)
- If MANAGER_STATE missing or empty, sets `context_used = "no prior state"`

Helpers: `_read_manager_state()`, `_extract_state_sections()`.  
State path: `MANAGER_STATE_PATH = /opt/concerto-workspace/OPS/MANAGER_STATE.md`

### 2. Envelope linter

After every `_run_claude` call completes:

```python
last_line = s["output_lines"][-1] if s["output_lines"] else ""
env_valid, env_parsed, env_reason = _validate_envelope(last_line)
s["envelope_valid"] = env_valid
s["envelope_parsed"] = env_parsed   # total_cost_usd stripped
s["envelope_reason"] = env_reason
```

- `_validate_envelope()` parses the last stdout line as JSON
- Checks `status` in `{"ok", "partial", "aborted", "failed"}`, `summary` is str,
  `artifacts` is dict
- Sets `session.envelope_valid` bool; stores parsed envelope or `None` on failure
- On invalid: raw output is still retained; `envelope_reason` has the failure code
- `get_claude_session` surfaces `envelope_valid` and `envelope_parsed`

### 3. State diff persisted

In `_run_claude`, MANAGER_STATE is hashed before and after the subprocess:

```python
before_content = _read_manager_state()
before_hash = hashlib.md5(before_content.encode()).hexdigest()
# ... subprocess runs ...
after_content = _read_manager_state()
after_hash = hashlib.md5(after_content.encode()).hexdigest()
if before_hash and after_hash and before_hash != after_hash:
    diff_lines = list(difflib.unified_diff(...))
    _append_state_diff(session_id, before_hash, after_hash, diff_text)
```

- Unified diff capped at 5000 characters
- Persisted to `STATE_DIFFS_PATH = /data/state_diffs.json` (or `/var/lib/concerto/state_diffs.json`)
- Capped at 500 most-recent entries
- Not exposed to customers; powers future "what changed since last week?" answers

### 4. `concerto_replan(previous_plan_id, feedback)`

New MCP tool. Loads the original request + MANAGER_STATE + feedback, runs the
planner, and stores the revised plan as a child of the original:

```python
new_plan["parent_plan_id"] = previous_plan_id
new_plan["feedback"] = feedback
```

- Returns `plan_id`, `parent_plan_id`, `workstreams`, `next_action`
- Does NOT automatically launch sessions — caller invokes `concerto_build` or
  `start_claude_session` with the revised workstreams
- Plans persisted to `PLANS_PERSIST_PATH = /data/plans_state.json`
- Audit trail: the `_plans` dict links child → parent across the plan graph

### 5. Project-implicit scoping

`concerto_build` calls `_detect_active_project(state_content)` before spawning:

```python
detected_project = _detect_active_project(state_content)
# ... returned in tool response as detected_project field ...
```

- Parses "## Active projects" section, returns first non-placeholder project name
- Strips markdown heading markers (`###`) and list markers (`-`, `*`)
- Name capped at 80 chars
- Returned as `detected_project` in `concerto_build` response so the
  conversational Claude can surface it ("continuing on crm-outreach…")
- When MANAGER_STATE has no real projects, returns `None` and the build
  proceeds without an assumed context

---

## Architecture summary

- **Transport:** FastMCP streamable HTTP, `127.0.0.1:9876`
- **Auth:** OAuth 2.1 Bearer tokens (built-in AS) OR legacy static token
- **Session state:** In-memory `_sessions` dict, persisted to disk on every change
- **Plan state:** In-memory `_plans` dict, persisted to `plans_state.json`
- **Heartbeat:** Background thread pings Concerto VPS status endpoint
- **Claude execution:** `claude -p` CLI via `anyio.run_process` (`_run_claude`)
- **ASGI wrapper:** `CombinedApp` handles OAuth paths directly, proxies to FastMCP

---

## Tools registered

| Tool | Purpose |
|------|---------|
| `concerto_build` | Plan + spawn parallel agents for a build request (state-aware) |
| `start_claude_session` | Spawn a single autonomous Claude Code agent |
| `list_claude_sessions` | List all sessions |
| `get_claude_session` | Poll a specific session (returns `envelope_valid`, `envelope_parsed`) |
| `kill_claude_session` | Kill a running session |
| `concerto_resume_session` | Resume a finished session with prior context |
| `concerto_replan` | Revise a previous plan with feedback; audit trail via `parent_plan_id` |
| `export_my_work` | Package user work as a downloadable archive |
| `github_*` | GitHub integration (PR, push, clone) |

---

## Tests

`backend/tests/test_continuity.py` — 36 tests, all passing as of 2026-05-23.

Coverage:
- `_extract_state_sections` (4 tests)
- `_detect_active_project` (5 tests)
- `_validate_envelope` (8 tests)
- `_append_state_diff` / state diff in `_run_claude` (3 tests)
- `concerto_build` state injection and plan persistence (4 tests)
- `concerto_replan` parent/child plan linking (4 tests)
- `concerto_resume_session` prior context loading (5 tests)
- Plan persistence helpers (2 tests)
- `_strip_cost_from_lines` (cost strip) — covered by rebuild-prep session

---

## Deploy path

Changes are code-level only in `installer/mcp_server.py`.  
No new pip dependencies. No DB schema changes.  
Ethan triggers rebuild per `/tmp/concerto-rebuild-prep/REBUILD_PLAN_2026_05_23.md`.

---

## Known limitations (as of 2026-05-23)

- `start_claude_session` (low-level tool) does not auto-inject MANAGER_STATE
  context; callers are expected to use `concerto_build` for state-aware launches
- `concerto_build` model default is still `claude-sonnet-4-5`; bump to
  `claude-sonnet-4-6` tracked as open question in REBUILD_PLAN
- No multi-account routing (single-account: the customer's VPS Claude CLI)
- Session state lost on runtime restart (by design — ephemeral per-VPS)
