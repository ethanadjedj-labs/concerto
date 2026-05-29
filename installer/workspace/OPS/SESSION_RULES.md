# Session Rules — read at the start of every spawned session

This file defines binding conventions for Claude Code sessions running on your Concerto VPS. Read it before doing substantive work.

## Read first in every session

1. `/opt/concerto-workspace/OPS/MANAGER_STATE.md` — strategic state, decisions, follow-ups
2. `/opt/concerto-workspace/OPS/SESSION_RULES.md` — this file
3. `/opt/concerto-workspace/OPS/ENVELOPE_SCHEMA.md` — return format
4. Check for `/opt/concerto-workspace/.first_run` — if it exists, follow the First-run welcome section before anything else.

## First-run welcome

If the file `/opt/concerto-workspace/.first_run` exists, this is the user's first session with Concerto. Before doing anything else:

1. Read `/opt/concerto-workspace/.first_run` to see the user's GitHub username (it contains one line: their `login`, e.g. `ethanadjedj`).
2. Greet the user with EXACTLY this message (substituting the username and home-base repo name):

   ```
   Welcome to Concerto. Your GitHub is connected and I've created a private repository called `concerto` on your account (github.com/<login>/concerto). This is our workspace - everything I build for you will be committed and pushed there automatically, so your work is always yours and always backed up.

   If you'd rather we work on a different repo of yours, just tell me which one. Otherwise, what would you like to build?
   ```

3. Delete `/opt/concerto-workspace/.first_run` so the welcome only fires once.

If `.first_run` does not exist, skip this section entirely.

## Language and communication

- Write session prompts in English.
- Keep prompt intent clear and specific. Include: goal, deliverables, acceptance criteria, abort conditions.
- Return envelopes per ENVELOPE_SCHEMA.md as the final stdout output of every session.

## Working directory

- Default working directory for sessions: `/opt/concerto-workspace/` or a subdirectory.
- Do not `cd /root` as working_dir; read from absolute paths if needed.
- Prefer idempotent operations. Before writing a file, check if it exists and the desired state is already achieved.

## GitHub workflow

- The user has a default home-base repo named `concerto` on their GitHub, auto-created during onboarding. Its full name (e.g. `octocat/concerto`) is in `/home/concerto/.concerto_home_repo` if available.
- Work-in-progress sessions commit and push to this repo by default at the end of substantive work.
- MCP tools available: `github_list_repos`, `github_active_repo`, `github_clone`, `github_switch_repo`, `github_status`, `github_view_file`, `github_commit_push`, `github_create_pr`, `github_pull`.
- Default to working in the active repo (read via `github_active_repo`). If the user asks to work on a different repo, use `github_switch_repo`.
- NEVER force-push.
- Commits directly to `main` or the default branch are forbidden by default. Use `github_commit_push`, which auto-creates a `claude/<kebab>` branch when on main.
- At the end of any session that produced material changes, run `github_commit_push` with a descriptive commit message.

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
