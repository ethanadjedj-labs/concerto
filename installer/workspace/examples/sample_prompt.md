# Sample Session Prompt

A well-formed session prompt gives the spawned Claude Code session everything it needs to work autonomously. Copy and adapt this template.

---

## Template

```
Read /opt/maestro-workspace/OPS/MANAGER_STATE.md and /opt/maestro-workspace/OPS/SESSION_RULES.md before starting.

## Goal

<One sentence: what outcome this session should produce.>

## Deliverables

- <Specific file, endpoint, or state change that must exist when done.>
- <Another deliverable.>

## Acceptance criteria

- <How to verify the work is correct. Be specific: a passing test, a working HTTP response, a file with expected content.>
- <Another criterion.>

## Working directory

/opt/maestro-workspace/<subdirectory>

## Abort conditions

- If RAM available drops below 200 MiB.
- If any required credential is missing from the environment.
- If a destructive operation not in this spec would be required.

## Return format

Print a JSON envelope as the final stdout line per /opt/maestro-workspace/OPS/ENVELOPE_SCHEMA.md.
```

---

## Notes

- The clearer the deliverables, the less the session will ask for clarification.
- Abort conditions protect against runaway sessions. Always include them.
- "Acceptance criteria" is what you would manually check — write it as if you'll verify it yourself.
- Sessions that update state should write back to MANAGER_STATE.md before printing their envelope.
