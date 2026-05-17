# Parallel Workflow — running multiple sessions at once

Maestro sessions are independent processes on your VPS. You can fire several in parallel from a single claude.ai message.

## Pattern

In one message, ask Claude to spawn N sessions simultaneously:

> Spawn 3 Maestro sessions in parallel:
> 1. Session "audit-backend": list all Python files in /opt/maestro-workspace/myapp/backend/ and report any files over 300 lines.
> 2. Session "check-deps": run `pip list --outdated` in /opt/maestro-workspace/myapp/ and report packages more than 2 major versions behind.
> 3. Session "test-suite": run `pytest /opt/maestro-workspace/myapp/tests/ -q` and return pass/fail counts.

Claude will call `start_claude_session` three times in sequence and return three session IDs.

## Monitoring

After spawning, Claude cannot poll (it ends its turn cleanly). Come back and ask:

> What did audit-backend, check-deps, and test-suite return?

Claude calls `get_claude_session` for each and surfaces the envelopes.

## Resource limits

Your Maestro VPS has 2 GiB RAM by default. Running more than 2-3 heavy sessions simultaneously risks OOM. For safe parallel limits:
- Light sessions (file reads, small scripts): up to 4 in parallel.
- Heavy sessions (npm install, large test suites, model inference): max 2 in parallel.

## Naming convention

Use descriptive names so sessions are easy to reference:
- Good: `audit-backend`, `test-api`, `seed-database`
- Bad: `session1`, `task`, `2026-05-17`

## When to use parallel sessions

- Independent work that doesn't share mutable state (different files, different repos)
- Fan-out: spawn many small sessions to gather data, then synthesize in a final session
- Staged pipelines: run stages 1-3 in parallel, then stage 4 depends on their output

## When NOT to use parallel sessions

- When sessions write to the same file or database without coordination
- When a later session needs output from an earlier one (use sequential sessions instead)
- When RAM is already constrained (check with `exec_on_vps: free -m`)
