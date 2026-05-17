# Session Rules — read at the start of every spawned session

This file defines binding conventions for Claude Code sessions running on your Concerto VPS. Read it before doing substantive work.

## Read first in every session

1. `/opt/concerto-workspace/OPS/MANAGER_STATE.md` — strategic state, decisions, follow-ups
2. `/opt/concerto-workspace/OPS/SESSION_RULES.md` — this file
3. `/opt/concerto-workspace/OPS/ENVELOPE_SCHEMA.md` — return format

## Language and communication

- Write session prompts in English.
- Keep prompt intent clear and specific. Include: goal, deliverables, acceptance criteria, abort conditions.
- Return envelopes per ENVELOPE_SCHEMA.md as the final stdout output of every session.

## Working directory

- Default working directory for sessions: `/opt/concerto-workspace/` or a subdirectory.
- Do not `cd /root` as working_dir; read from absolute paths if needed.
- Prefer idempotent operations. Before writing a file, check if it exists and the desired state is already achieved.

## GitHub and git (if you have a repo wired up)

- Branch names: `claude/<short-kebab-task>` (e.g. `claude/add-auth-endpoint`).
- Commit identity: set `user.email` and `user.name` per-repo before committing if not already set.
- Never force-push without explicit operator approval.
- Merge via `gh pr merge --admin --squash` if CI is not configured.
- If GitHub auth fails: check that `GH_TOKEN` is set in your environment, or run `gh auth login`.

## State hygiene

- When a session changes consequential state (new file, migrated DB, deployed service), update MANAGER_STATE.md before closing.
- Write pending operator decisions to MANAGER_STATE.md under "Pending operator decisions".
- Keep session scope focused. If scope creep arises, flag it and open a separate session rather than drifting.

## Resource caveats

- Concerto VPS runs on a 2 GiB RAM droplet by default. Max 2 parallel Claude sessions is safe.
- Abort and report if available RAM drops below 200 MiB.

## Universal abort triggers

- VPS RAM available drops below 200 MiB → stop and report.
- Auth issues not resolved by checking env vars → stop and report.
- Destructive operation (rm -rf, drop table, force-push) not in the original task spec → stop and ask.

## Output discipline

- Every session ends by printing its envelope (JSON) to stdout per ENVELOPE_SCHEMA.md.
- PR titles: conventional commits format (`fix(scope): ...`, `feat(scope): ...`).
- Branch names: `claude/<short-kebab-case-task>`.
