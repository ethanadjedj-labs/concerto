# Envelope Schema — final JSON output of every spawned session

Every Claude Code session spawned via `start_claude_session` should print, as its FINAL stdout line, a JSON object on a single line. This envelope is parsed by your main claude.ai conversation to understand what the session accomplished without re-reading the full log.

## Shape

```json
{
  "status": "ok | partial | aborted | failed",
  "summary": "<1-3 sentence human readable>",
  "artifacts": {
    "files_created": ["path/to/new_file"],
    "files_modified": ["path/to/changed_file"],
    "pr_url": "https://github.com/...",
    "commits": ["<full-sha>"]
  },
  "next_recommended": "<free text: what to do next>",
  "decisions_for_operator": [
    {"question": "<closed yes/no or A vs B>", "context": "<1 line>"}
  ],
  "errors": []
}
```

## Field rules

- **`status`**: `ok` = all criteria met; `partial` = some met but at least one failed; `aborted` = hit abort trigger; `failed` = unexpected error.
- **`summary`**: 1-3 sentences for the operator. What was done, what changed.
- **`artifacts`**: only include fields that have values. Omit empty arrays.
- **`next_recommended`**: free text. What the operator or next session should do.
- **`decisions_for_operator`**: only include if operator must answer before next task proceeds. Closed questions only.
- **`errors`**: empty list if `status: ok`. One item per failure with a recovery hint.

## Output discipline

- Print the envelope as the very last stdout line. No markdown fences, no preamble.
- Single line (no embedded newlines outside string values) so it parses cleanly.
- Write human-readable output before the envelope; envelope is always last.
