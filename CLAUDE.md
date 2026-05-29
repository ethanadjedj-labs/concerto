# Cortex Ecosystem Session

## You are on the Cortex VPS
You're a spawned Claude Code session. The MCP `cortex-vps-bridge` (URL-bound) is NOT
for you — you have direct Bash/Read/Write access locally. Use those.

## Memory layer (READ FIRST)
Query unacked inbox events for this project:
  sqlite3 /var/lib/cortex/cortex.db "SELECT id,kind,payload_json FROM claude_inbox WHERE project='concerto' AND acked_at IS NULL ORDER BY created_at;"

Read project state:
  sqlite3 /var/lib/cortex/cortex.db "SELECT manager_state_md FROM project_states WHERE project='concerto';"

## When you finish
- Append a session_done (or session_failed) event to claude_inbox:
  sqlite3 /var/lib/cortex/cortex.db "INSERT INTO claude_inbox(created_at,actor,project,kind,payload_json) VALUES(strftime('%s','now'),'system','concerto','session_done',json_object('session_id','sess_20260523T110234Z_5bddb8','summary','<summary>'));"
- If you changed consequential project state, run: /opt/cortex/ops/state_write.sh concerto "<one-line change summary>"
- Print the JSON envelope per /opt/cortex/OPS/ENVELOPE_SCHEMA.md as the final stdout line.

## Project context
- Project: concerto
- Spawn parent: none
- Actor: 45157e50a1df
