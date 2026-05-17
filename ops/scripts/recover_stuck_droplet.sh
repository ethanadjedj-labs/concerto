#!/usr/bin/env bash
# recover_stuck_droplet.sh — force a buyer stuck in 'provisioning' or 'installing' back to a
# re-provisionable state so they can retry. Does NOT destroy the droplet (use
# force_refund_buyer.sh for that).
#
# Usage:
#   ./recover_stuck_droplet.sh <buyer_token>
#
# Safe to re-run. Idempotent.

set -euo pipefail

DB=/var/lib/concerto/concerto.db
TOKEN="${1:?Usage: $0 <buyer_token>}"

# Validate token exists
STATUS=$(sqlite3 "$DB" "SELECT status FROM concerto_buyers WHERE token='$TOKEN';" 2>/dev/null || true)
if [ -z "$STATUS" ]; then
  echo "ERROR: token '$TOKEN' not found in DB" >&2
  exit 1
fi

echo "Current status: $STATUS"

case "$STATUS" in
  provisioning|installing|provisioning_timeout|provisioning_failed|failed_install)
    sqlite3 "$DB" \
      "UPDATE concerto_buyers
       SET status='provisioning_failed',
           failure_reason='Manually reset by operator via recover_stuck_droplet.sh at $(date -u +%Y-%m-%dT%H:%M:%SZ)'
       WHERE token='$TOKEN';"
    echo "OK — status set to 'provisioning_failed'. Customer can now retry via /setup/$TOKEN"
    ;;
  paid_unprovisioned)
    echo "Nothing to do — buyer is already in retriable state 'paid_unprovisioned'"
    ;;
  refunded|suspended)
    echo "WARNING: buyer is '$STATUS' — re-provisioning would give product without payment. Aborting." >&2
    exit 2
    ;;
  *)
    echo "WARNING: status='$STATUS' is not a stuck state. No change made."
    echo "If you really want to reset, run:"
    echo "  sqlite3 $DB \"UPDATE concerto_buyers SET status='provisioning_failed' WHERE token='$TOKEN';\""
    ;;
esac

echo ""
echo "Current buyer row:"
sqlite3 "$DB" ".headers on" ".mode column" \
  "SELECT token, email, plan, status, vps_id, vps_ip, failure_reason FROM concerto_buyers WHERE token='$TOKEN';"
