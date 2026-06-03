#!/bin/bash
# Concerto multi-target healthcheck — polls backend, frontend, and public /trial.
# Tracks failure counts separately per target; restarts the relevant service
# after 3 consecutive failures. Alerts via claude_inbox event bus (not email).
#
# Targets monitored:
#   backend  — http://127.0.0.1:8090/healthz  (restarts concerto-backend.service)
#   frontend — http://127.0.0.1:3500/         (restarts concerto-frontend.service)
#   trial    — https://concerto.run/trial      (alert only, no restart)
#
# State files (separate failure count + alert sentinel per target):
#   /var/lib/concerto/healthcheck-failures-{backend,frontend,trial}
#   /var/lib/concerto/healthcheck-alert-{backend,frontend,trial}
set -euo pipefail

LOG=/var/log/concerto-healthcheck.log
CORTEX_DB=/var/lib/cortex/cortex.db

# ── inbox alert helper ────────────────────────────────────────────────────────
# Writes a service_alert or service_recovery event to claude_inbox so it
# surfaces in orchestrator chat. The cortex DB may be protected by ProtectSystem
# in the monitoring service, so we use a transient unit with ProtectSystem=no.
inbox_alert() {
    local kind="$1"       # service_alert or service_recovery
    local severity="$2"   # critical or info
    local target="$3"
    local http_code="$4"
    local detail="$5"
    local ts
    ts=$(date -u +%FT%TZ)
    # Build JSON payload safely via python
    local payload
    payload=$(python3 -c "
import json, sys
print(json.dumps({
    'severity': sys.argv[1],
    'target':   sys.argv[2],
    'http_code': sys.argv[3],
    'detail':   sys.argv[4],
    'ts':       sys.argv[5],
}))" "$severity" "$target" "$http_code" "$detail" "$ts" 2>/dev/null) || return 0
    # Escape single quotes in payload for sqlite literal
    local payload_sq="${payload//\'/\'\'}"
    systemd-run --quiet --pipe --wait \
        --property=ProtectSystem=no \
        --property=ProtectHome=no \
        sqlite3 "$CORTEX_DB" \
        "INSERT INTO claude_inbox(created_at,actor,project,kind,payload_json) VALUES(strftime('%s','now'),'concerto-healthcheck','concerto','${kind}','${payload_sq}')" \
        >> "$LOG" 2>&1 || true
}

# ── per-target check ──────────────────────────────────────────────────────────
# Args: target url expected_code service_or_empty [max_failures=3]
check_target() {
    local target="$1"
    local url="$2"
    local expected="$3"
    local service="$4"
    local max_fail="${5:-3}"

    local state_file="/var/lib/concerto/healthcheck-failures-${target}"
    local alert_file="/var/lib/concerto/healthcheck-alert-${target}"

    [ -f "$state_file" ] || echo "0" > "$state_file"

    local http
    http=$(curl -sSL -o /dev/null -w "%{http_code}" --max-time 12 "$url" 2>/dev/null || echo "000")

    local fail_count
    fail_count=$(cat "$state_file")

    if [ "$http" = "$expected" ]; then
        echo "0" > "$state_file"
        if [ -f "$alert_file" ]; then
            local alert_ts ts
            alert_ts=$(cat "$alert_file")
            ts=$(date -u +%FT%TZ)
            rm -f "$alert_file"
            echo "$ts [${target}] RECOVERED (alert started $alert_ts)" >> "$LOG"
            inbox_alert "service_recovery" "info" "$target" "$http" \
                "Recovered at ${ts}; alert had started at ${alert_ts}"
        fi
        return 0
    fi

    fail_count=$((fail_count + 1))
    echo "$fail_count" > "$state_file"
    local ts
    ts=$(date -u +%FT%TZ)
    echo "$ts [${target}] FAIL HTTP=${http} count=${fail_count} url=${url}" >> "$LOG"

    if [ "$fail_count" -ge "$max_fail" ]; then
        echo "$ts [${target}] ALERT: ${max_fail}+ consecutive failures (HTTP=${http})" >> "$LOG"
        if [ -n "$service" ]; then
            systemctl restart "$service" >> "$LOG" 2>&1 || true
            echo "$ts [${target}] restarted ${service}" >> "$LOG"
        fi
        echo "0" > "$state_file"
        if [ ! -f "$alert_file" ]; then
            echo "$ts" > "$alert_file"
            local restarted="no"
            [ -n "$service" ] && restarted="yes"
            inbox_alert "service_alert" "critical" "$target" "$http" \
                "${max_fail}+ consecutive failures; service=${service:-none}; restarted=${restarted}"
        fi
    fi
}

# ── run all three checks ──────────────────────────────────────────────────────
check_target "backend"  "http://127.0.0.1:8090/healthz" "200" "concerto-backend.service"
check_target "frontend" "http://127.0.0.1:3500/"         "200" "concerto-frontend.service"
check_target "trial"    "https://concerto.run/trial"     "200" ""
