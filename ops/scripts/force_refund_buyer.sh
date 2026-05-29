#!/usr/bin/env bash
# force_refund_buyer.sh — manually mark a buyer as refunded, optionally destroy their hosted
# droplet, and update the DB. Does NOT issue the Stripe refund automatically (do that in the
# Stripe dashboard for auditability). Sends no email — do that manually.
#
# Usage:
#   ./force_refund_buyer.sh <buyer_token> [--destroy-droplet]
#
# Flags:
#   --destroy-droplet   Also destroy the DigitalOcean droplet via the API (requires CONCERTO_DO_API_TOKEN)
#
# Safe to re-run on already-refunded buyers (no-op).

set -euo pipefail

DB=/var/lib/concerto/concerto.db
TOKEN="${1:?Usage: $0 <buyer_token> [--destroy-droplet]}"
DESTROY_DROPLET=0

for arg in "$@"; do
  if [ "$arg" = "--destroy-droplet" ]; then
    DESTROY_DROPLET=1
  fi
done

# Look up buyer
ROW=$(sqlite3 "$DB" ".headers on" ".mode line" \
  "SELECT token, email, plan, status, vps_id, refunded_at FROM concerto_buyers WHERE token='$TOKEN';" 2>/dev/null || true)

if [ -z "$ROW" ]; then
  echo "ERROR: token '$TOKEN' not found in DB" >&2
  exit 1
fi

echo "=== Current buyer ==="
echo "$ROW"
echo ""

STATUS=$(sqlite3 "$DB" "SELECT status FROM concerto_buyers WHERE token='$TOKEN';")
if [ "$STATUS" = "refunded" ]; then
  echo "Buyer is already refunded. Nothing to do."
  exit 0
fi

# Destroy droplet if requested
VPS_ID=$(sqlite3 "$DB" "SELECT vps_id FROM concerto_buyers WHERE token='$TOKEN';")
if [ "$DESTROY_DROPLET" = "1" ] && [ -n "$VPS_ID" ] && [ "$VPS_ID" != "NULL" ]; then
  DO_TOKEN=$(grep CONCERTO_DO_API_TOKEN /etc/cortex/env 2>/dev/null | cut -d= -f2 || echo "")
  if [ -z "$DO_TOKEN" ]; then
    echo "ERROR: CONCERTO_DO_API_TOKEN not found in /etc/cortex/env — cannot destroy droplet" >&2
    exit 1
  fi
  echo "Destroying droplet $VPS_ID..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    -H "Authorization: Bearer $DO_TOKEN" \
    "https://api.digitalocean.com/v2/droplets/$VPS_ID")
  if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "404" ]; then
    echo "Droplet $VPS_ID destroyed (HTTP $HTTP_CODE)"
  else
    echo "WARNING: unexpected HTTP $HTTP_CODE from DO API — check droplet manually at cloud.digitalocean.com"
  fi
fi

# Mark as refunded in DB
NOW=$(date +%s)
sqlite3 "$DB" \
  "UPDATE concerto_buyers
   SET status='refunded',
       refunded_at=$NOW,
       failure_reason='Manually refunded by operator via force_refund_buyer.sh at $(date -u +%Y-%m-%dT%H:%M:%SZ)'
   WHERE token='$TOKEN';"

echo ""
echo "=== Done ==="
echo "Buyer marked as refunded in DB."
echo ""
echo "NEXT STEPS (manual):"
echo "  1. Issue Stripe refund: https://dashboard.stripe.com/payments"
echo "     - Find payment by customer email, click 'Refund'"
echo "  2. Send refund email to customer (template in RUNBOOK.md §8.2)"
echo ""
echo "Updated buyer:"
sqlite3 "$DB" ".headers on" ".mode column" \
  "SELECT token, email, plan, status, vps_id, refunded_at FROM concerto_buyers WHERE token='$TOKEN';"
