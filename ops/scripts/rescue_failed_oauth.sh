#!/usr/bin/env bash
# rescue_failed_oauth.sh — rescue a buyer who is stuck in 'awaiting_oauth' without credentials.
# Re-sends the setup email with the dashboard URL so the customer can re-try the OAuth step.
#
# Usage:
#   ./rescue_failed_oauth.sh <buyer_token>
#
# Does:
#   1. Verifies buyer exists and is in 'awaiting_oauth' state
#   2. Clears dashboard_opened_at so next visit is counted as fresh
#   3. Prints the curl command to re-send the welcome email via the backend (if Resend is wired)
#   4. Optionally SSH-checks the droplet OAuth state to help diagnose
#
# Safe to re-run. Does not modify credentials or droplet state.

set -euo pipefail

DB=/var/lib/concerto/concerto.db
TOKEN="${1:?Usage: $0 <buyer_token>}"

# Look up buyer
ROW=$(sqlite3 "$DB" ".headers on" ".mode line" \
  "SELECT token, email, plan, status, vps_ip, mcp_url, dashboard_opened_at, first_call_at \
   FROM concerto_buyers WHERE token='$TOKEN';" 2>/dev/null || true)

if [ -z "$ROW" ]; then
  echo "ERROR: token '$TOKEN' not found in DB" >&2
  exit 1
fi

echo "=== Current buyer ==="
echo "$ROW"
echo ""

STATUS=$(sqlite3 "$DB" "SELECT status FROM concerto_buyers WHERE token='$TOKEN';")
EMAIL=$(sqlite3 "$DB" "SELECT email FROM concerto_buyers WHERE token='$TOKEN';")
VPS_IP=$(sqlite3 "$DB" "SELECT vps_ip FROM concerto_buyers WHERE token='$TOKEN';")
KEY_PATH=$(sqlite3 "$DB" "SELECT ssh_keypair_private_path FROM concerto_buyers WHERE token='$TOKEN';")

if [ "$STATUS" != "awaiting_oauth" ]; then
  echo "WARNING: buyer status is '$STATUS', not 'awaiting_oauth'."
  echo "This script is intended for stuck OAuth cases. Check the actual status."
fi

# SSH check if we have a key
if [ -n "$VPS_IP" ] && [ -n "$KEY_PATH" ] && [ -f "$KEY_PATH" ]; then
  echo "=== SSH OAuth check on droplet $VPS_IP ==="
  ssh -i "$KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=8 \
    -o BatchMode=yes \
    "root@$VPS_IP" \
    "bash -c 'if [ -f ~/.claude/.credentials.json ]; then echo \"OAUTH: FOUND\"; else echo \"OAUTH: MISSING\"; fi; claude --version 2>/dev/null || echo \"claude: NOT INSTALLED\"; systemctl is-active concerto-mcp concerto-ttyd concerto-tunnel'" 2>/dev/null || echo "(SSH failed — droplet may be unreachable)"
  echo ""
fi

# Reset dashboard_opened_at so next visit registers as first open (triggers 24h reminder)
sqlite3 "$DB" \
  "UPDATE concerto_buyers SET dashboard_opened_at=NULL WHERE token='$TOKEN';"
echo "Cleared dashboard_opened_at — next visit will be counted as fresh."

DASHBOARD_URL="https://concerto.run/dashboard/$TOKEN"
echo ""
echo "=== Action: re-send setup email to $EMAIL ==="
echo "Run the following from the empire VPS:"
echo ""
echo "  curl -s -X POST https://api.resend.com/emails \\"
echo "    -H 'Authorization: Bearer \$(grep RESEND_API_KEY /etc/cortex/env | cut -d= -f2)' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{"
echo "      \"from\": \"hello@concerto.run\","
echo "      \"to\": [\"$EMAIL\"],"
echo "      \"subject\": \"Your Concerto workspace is ready — complete OAuth\","
echo "      \"html\": \"<p>Hi,</p><p>Your Concerto workspace is ready. Click below to access your dashboard and complete the Claude OAuth step:</p><p><a href=\\\\\"$DASHBOARD_URL\\\\\">Open My Concerto Dashboard</a></p><p>If you have trouble, reply to this email.</p>\""
echo "    }'"
echo ""
echo "=== Dashboard URL for this buyer ==="
echo "$DASHBOARD_URL"
