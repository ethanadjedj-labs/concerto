# Maestro Workspace

This is your Maestro workspace root. Claude Code sessions spawned from claude.ai land here.

## Read at the start of every session

1. `OPS/MANAGER_STATE.md` — what you are building, active projects, open decisions
2. `OPS/SESSION_RULES.md` — conventions for this workspace
3. `OPS/ENVELOPE_SCHEMA.md` — how to format your final output

## After substantive work

Update `OPS/MANAGER_STATE.md` with what changed and what is pending before closing.

## Working directory

Stay in `/opt/maestro-workspace/` or subdirectories. Avoid using `/root` as working_dir.

## Output discipline

End every session by printing a JSON envelope to stdout per `OPS/ENVELOPE_SCHEMA.md`.
