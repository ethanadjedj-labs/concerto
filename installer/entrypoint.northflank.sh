#!/bin/sh
# Concerto Northflank container entrypoint.
#
# Addresses critical gaps from result-dockerfile.md:
#   [GAP-1] Secrets injection: all secrets read from env vars injected by
#           Northflank runtimeEnvironment at service creation time.
#           See provider_northflank.py _build_env_vars for the full list.
#   [GAP-2] Bearer-token callback: container POSTs BEARER_TOKEN + mcp_url +
#           ttyd_url to CONCERTO_CALLBACK_URL so the backend DB is populated.
#           Same function as cloud_init provision_complete.sh on DO.
#   [GAP-4] Claude auth: ANTHROPIC_API_KEY written to Claude settings if set.
#           CONFIG TODO: prefer NF project secret group over per-service injection.
#   [GAP-5] Git credentials polling: polls backend every 30s if GIT_CREDS_POLL_URL
#           is set. CONFIG TODO: confirm endpoint path with backend team.
#
# Gaps that are deploy-time config (not addressed here):
#   [GAP-1-CRED] Private registry credential ID: set CONCERTO_NF_IMAGE_CRED_ID
#                in /etc/cortex/env and the Northflank console.
#   [GAP-3-TUNNEL] Cloudflare vs native URL: native NF URL used by default.
#                  To use CF tunnels: install cloudflared in image, start it here
#                  with TUNNEL_TOKEN, and set mcp_url/ttyd_url to TUNNEL_HOSTNAME.

set -e

echo "[entrypoint] Starting Concerto Northflank container..."
echo "[entrypoint] claude version: $(claude --version 2>&1)"

# ── Persist /home/concerto on /data volume ───────────────────────────────────
# Without this, Claude's code (in /home/concerto/<project>) is on the
# container's ephemeral filesystem and is wiped on every container restart.
# Strategy: keep the actual directory tree on /data/home-concerto and replace
# /home/concerto with a symlink to it.
if [ -d /data ] && [ -w /data ]; then
    mkdir -p /data/home-concerto
    if [ ! -L /home/concerto ]; then
        # First boot OR an old container without symlink: migrate any existing
        # files from /home/concerto into /data/home-concerto, then symlink.
        if [ -d /home/concerto ] && [ "$(ls -A /home/concerto 2>/dev/null)" ]; then
            cp -a /home/concerto/. /data/home-concerto/ 2>/dev/null || true
        fi
        rm -rf /home/concerto
        ln -s /data/home-concerto /home/concerto
    fi
    # Ensure ownership of the data dir (the symlink itself doesn't need chown)
    chown -R concerto:concerto /data/home-concerto 2>/dev/null || true
    chmod 755 /data/home-concerto 2>/dev/null || true
    echo "[entrypoint] /home/concerto persisted on /data volume"
else
    echo "[entrypoint] WARNING: /data not available — /home/concerto on ephemeral fs"
fi

# ── Read secrets from env (injected by Northflank at service create) ──────────
CONCERTO_TOKEN="${CONCERTO_TOKEN:-}"
BEARER_TOKEN="${BEARER_TOKEN:-}"
TTYD_PASSWORD="${TTYD_PASSWORD:-changeme-set-TTYD_PASSWORD}"
CONCERTO_CALLBACK_URL="${CONCERTO_CALLBACK_URL:-}"
NF_PUBLIC_URL="${NF_PUBLIC_URL:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
# CONFIG TODO: Set GIT_CREDS_POLL_URL to the backend endpoint that returns
# the customer's GitHub token, e.g.:
#   https://api.concerto.run/api/internal/git-creds
GIT_CREDS_POLL_URL="${GIT_CREDS_POLL_URL:-}"

# ── Write BEARER_TOKEN to /etc/concerto/token (MCP server reads this file) ───
# DO path: cloud_init generates `openssl rand -hex 32 > /etc/concerto/token`
# NF path: token is pre-generated server-side and injected via BEARER_TOKEN env var.
# The MCP server (_read_token) reads this file for legacy static bearer auth.
if [ -n "$BEARER_TOKEN" ]; then
    printf '%s' "$BEARER_TOKEN" > /etc/concerto/token
    chmod 600 /etc/concerto/token
    echo "[entrypoint] Bearer token written to /etc/concerto/token"
fi

# ── [GAP-4] Claude authentication ────────────────────────────────────────────
# Two paths for Claude auth (see provider_northflank.py _build_env_vars):
#
#   Path A (default): ANTHROPIC_API_KEY is NOT injected per-service.
#     Customer authenticates by running `claude login` in the ttyd terminal.
#     This matches existing DO behavior. No action needed here.
#
#   Path B (opt-in): Set CONCERTO_NF_INJECT_ANTHROPIC_KEY=1 on the empire
#     backend. The provider will propagate ANTHROPIC_API_KEY from the backend
#     env into this service's runtimeEnvironment at provision time, and the
#     block below writes it into Claude's settings file.
#     Risk: the key appears in the per-customer NF service env listing.
#     Safer alternative: NF project secret group (dashboard) — attaches the
#     key at the project level so it never appears in per-service listings.
#
if [ -n "$ANTHROPIC_API_KEY" ]; then
    mkdir -p /home/concerto/.claude /root/.claude
    printf '{"primaryApiKey":"%s"}\n' "$ANTHROPIC_API_KEY" \
        > /home/concerto/.claude/settings.json
    printf '{"primaryApiKey":"%s"}\n' "$ANTHROPIC_API_KEY" \
        > /root/.claude/settings.json
    chown -R concerto:concerto /home/concerto/.claude 2>/dev/null || true
    echo "[entrypoint] Claude API key configured"
else
    echo "[entrypoint] WARNING: ANTHROPIC_API_KEY not set — claude commands will not authenticate"
fi

# ── 1. Start nginx and MCP server in parallel ─────────────────────────────────
# nginx starts as a daemon (returns immediately); MCP runs in background.
# Both start simultaneously — nginx serves port 8080, MCP binds 127.0.0.1:9876.
nginx
echo "[entrypoint] nginx started on port 8080"

# mcp_server.py has no module-level `app`; its main() calls uvicorn.run()
# with host=127.0.0.1, port=9876. Run it directly rather than via uvicorn CLI.
/opt/concerto/.venv/bin/python /opt/concerto/mcp_server.py &
MCP_PID=$!
echo "[entrypoint] MCP server started (PID $MCP_PID)"

# Wait for MCP server to be ready (max 20s).
MCP_READY=0
for i in $(seq 1 20); do
    if curl -sf http://127.0.0.1:9876/healthz >/dev/null 2>&1; then
        MCP_READY=1
        break
    fi
    sleep 1
done
if [ "$MCP_READY" = "1" ]; then
    echo "[entrypoint] MCP server ready (healthz OK after ${i}s)"
else
    echo "[entrypoint] WARNING: MCP server not responding after 20s — continuing anyway"
fi

# ── Cloudflare quick tunnel ──────────────────────────────────────────────────
# Same approach as the DO trial path: cloudflared tunnel --url http://127.0.0.1:8080
# gives us a public https://xxx.trycloudflare.com URL that points directly at
# nginx → MCP server, with Host header pass-through. This means the MCP server
# advertises *.trycloudflare.com in its OAuth metadata and Claude.ai talks to
# the same hostname end-to-end (no proxy host-rewriting issues).
mkdir -p /var/log
TUNNEL_URL=""
# Persist the tunnel URL across restarts via /data (NF persistent volume).
if [ -f /data/tunnel_url ]; then
    SAVED_URL=$(cat /data/tunnel_url 2>/dev/null | tr -d '[:space:]')
    # Saved URL may be a previous tunnel which is no longer valid (quick
    # tunnels are ephemeral and tied to the cloudflared process). Always
    # start a fresh one — but if the new scrape fails we'll fall back to
    # the saved URL below.
    echo "[entrypoint] Saved tunnel URL: $SAVED_URL"
fi
# Named tunnel (trial/solo/pro): use the pre-provisioned CF tunnel so the
# customer gets a stable c{hash}.concerto.run URL. Quick tunnel fallback only
# if TUNNEL_TOKEN is not provided.
if [ -n "$TUNNEL_TOKEN" ] && [ -n "$TUNNEL_HOSTNAME" ]; then
    echo "[entrypoint] Starting cloudflared NAMED tunnel: $TUNNEL_HOSTNAME"
    nohup cloudflared tunnel --no-autoupdate run --token "$TUNNEL_TOKEN" \
        > /var/log/cloudflared.log 2>&1 &
    CFD_PID=$!
    echo "[entrypoint] cloudflared started (PID $CFD_PID)"
    TUNNEL_URL="https://${TUNNEL_HOSTNAME}"
    # Wait until tunnel registers (up to 30s) — poll the cloudflared log for
    # "Registered tunnel connection" or just wait a bit.
    for i in $(seq 1 30); do
        if grep -qE "Registered tunnel connection|Updated to new configuration" /var/log/cloudflared.log 2>/dev/null; then
            echo "[entrypoint] Named tunnel registered"
            break
        fi
        sleep 1
    done
else
    echo "[entrypoint] No TUNNEL_TOKEN — falling back to cloudflared quick tunnel"
    nohup cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8080 \
        > /var/log/cloudflared.log 2>&1 &
    CFD_PID=$!
    echo "[entrypoint] cloudflared started (PID $CFD_PID)"
    # Scrape the trycloudflare URL from the log (max 30s)
    for i in $(seq 1 60); do
        if [ -f /var/log/cloudflared.log ]; then
            TUNNEL_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /var/log/cloudflared.log 2>/dev/null | head -1 || true)
        fi
        [ -n "$TUNNEL_URL" ] && break
        sleep 0.5
    done
fi

if [ -n "$TUNNEL_URL" ]; then
    echo "[entrypoint] Tunnel URL: $TUNNEL_URL"
    echo "$TUNNEL_URL" > /data/tunnel_url 2>/dev/null || true
elif [ -n "$SAVED_URL" ]; then
    echo "[entrypoint] WARNING: tunnel scrape failed, reusing saved URL: $SAVED_URL"
    TUNNEL_URL="$SAVED_URL"
else
    echo "[entrypoint] ERROR: no tunnel URL after 30s — Claude.ai will not be reachable"
    tail -20 /var/log/cloudflared.log || true
fi

# ── [GAP-2] Bearer-token callback ─────────────────────────────────────────────
# POST BEARER_TOKEN + mcp_url + ttyd_url to backend so DB gets populated.
# mcp_url = TUNNEL_URL/mcp (nginx proxies to MCP:9876 with Host pass-through).
echo "[entrypoint] env check: CONCERTO_TOKEN=${#CONCERTO_TOKEN}c BEARER_TOKEN=${#BEARER_TOKEN}c CALLBACK_URL=${CONCERTO_CALLBACK_URL}"
if [ -n "$CONCERTO_CALLBACK_URL" ] && [ -n "$BEARER_TOKEN" ] && [ -n "$CONCERTO_TOKEN" ]; then
    if [ -n "$TUNNEL_URL" ]; then
        MCP_URL="${TUNNEL_URL}/mcp"
        TTYD_URL="${TUNNEL_URL}/"
    else
        # Fallback: use the NF internal URL. Claude.ai connection will fail
        # (host mismatch in OAuth metadata) but at least the buyer record
        # is populated so the operator can investigate.
        MCP_URL="${NF_PUBLIC_URL}/mcp"
        TTYD_URL="${NF_PUBLIC_URL}/"
    fi
    curl -sf \
        --max-time 30 \
        -X POST "${CONCERTO_CALLBACK_URL}" \
        -H "Content-Type: application/json" \
        -H "X-Callback-Secret: ${CALLBACK_SECRET:-${TTYD_PASSWORD}}" \
        -d "{
              \"token\": \"${CONCERTO_TOKEN}\",
              \"bearer_token\": \"${BEARER_TOKEN}\",
              \"mcp_url\": \"${MCP_URL}\",
              \"ttyd_url\": \"${TTYD_URL}\"
            }" \
        && echo "[entrypoint] Bearer-token callback succeeded (mcp_url=$MCP_URL)" \
        || echo "[entrypoint] WARNING: Bearer-token callback failed — backend DB not updated"
else
    echo "[entrypoint] Skipping bearer-token callback (missing CONCERTO_TOKEN, BEARER_TOKEN, or CONCERTO_CALLBACK_URL)"
fi

# Restore persisted GitHub credentials from /data on boot.
if [ -f /data/git-credentials ]; then
    cp /data/git-credentials /home/concerto/.git-credentials
    chmod 600 /home/concerto/.git-credentials
    chown concerto:concerto /home/concerto/.git-credentials 2>/dev/null || true
    HOME=/home/concerto git config --global credential.helper store 2>/dev/null || true
    cp /data/git-credentials /root/.git-credentials
    chmod 600 /root/.git-credentials
    git config --global credential.helper store 2>/dev/null || true
    echo "[entrypoint] Restored GitHub credentials from /data"
fi

# ── [GAP-5] Git credentials polling ──────────────────────────────────────────
# Polls backend every 30s for the customer's GitHub token and writes it to
# ~/.git-credentials so `git push` works from the terminal.
# CONFIG TODO: Set GIT_CREDS_POLL_URL to the backend endpoint path.
if [ -n "$GIT_CREDS_POLL_URL" ] && [ -n "$CONCERTO_TOKEN" ]; then
    (
        while true; do
            RESPONSE=$(
                curl -sf --max-time 10 \
                    -H "X-Callback-Secret: ${CALLBACK_SECRET:-${TTYD_PASSWORD}}" \
                    "${GIT_CREDS_POLL_URL}?token=${CONCERTO_TOKEN}" \
                    2>/dev/null \
                || true
            )
            GH_TOKEN=$(echo "$RESPONSE" | python3 -c \
                "import sys,json; d=json.load(sys.stdin); print(d.get('github_token',''))" \
                2>/dev/null || true)
            CONCERTO_REPO=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('concerto_repo',''))" 2>/dev/null || true)
            GITHUB_LOGIN=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('github_login',''))" 2>/dev/null || true)
            if [ -n "$GH_TOKEN" ]; then
                # Claude Code runs as 'concerto' user, so credentials need to
                # live in /home/concerto, not /root. Also persist to /data so
                # restarts work immediately (before the next poll cycle).
                CRED_LINE="https://token:${GH_TOKEN}@github.com"
                # concerto user (the one Claude Code uses)
                printf '%s\n' "$CRED_LINE" > /home/concerto/.git-credentials
                chmod 600 /home/concerto/.git-credentials
                chown concerto:concerto /home/concerto/.git-credentials 2>/dev/null || true
                HOME=/home/concerto git config --global credential.helper store 2>/dev/null || true
                # Mirror for root
                printf '%s\n' "$CRED_LINE" > /root/.git-credentials
                chmod 600 /root/.git-credentials
                git config --global credential.helper store 2>/dev/null || true
                # Persist to /data for restart resilience
                printf '%s\n' "$CRED_LINE" > /data/git-credentials 2>/dev/null || true
            fi
            if [ -n "$CONCERTO_REPO" ]; then
                HOME_REPO_FILE=/home/concerto/.concerto_home_repo
                FIRST_RUN_FILE=/opt/concerto-workspace/.first_run

                # Idempotent: only mark as first_run if home_repo file did NOT previously exist.
                NEEDS_FIRST_RUN=0
                if [ ! -f "$HOME_REPO_FILE" ]; then
                    NEEDS_FIRST_RUN=1
                fi

                # Write home repo file (overwrite is fine if same value, ensures fresh content).
                mkdir -p /opt/concerto-workspace
                printf '%s\n' "$CONCERTO_REPO" > "$HOME_REPO_FILE"
                chmod 644 "$HOME_REPO_FILE"
                chown concerto:concerto "$HOME_REPO_FILE" 2>/dev/null || true

                # Clone the home-base repo into /opt/concerto-workspace/repos/<owner>__<name>
                # if not yet cloned. Use the credential helper that the container already
                # configured for git (~/.git-credentials).
                OWNER=$(echo "$CONCERTO_REPO" | cut -d/ -f1)
                REPO_NAME=$(echo "$CONCERTO_REPO" | cut -d/ -f2)
                CLONE_DIR=/opt/concerto-workspace/repos/${OWNER}__${REPO_NAME}
                if [ ! -d "$CLONE_DIR/.git" ]; then
                    mkdir -p /opt/concerto-workspace/repos
                    sudo -u concerto -H git clone "https://github.com/${CONCERTO_REPO}.git" "$CLONE_DIR" 2>&1 | tee -a /var/log/concerto-clone.log || true
                    # Set active repo pointer
                    printf '%s\n' "$CONCERTO_REPO" > /opt/concerto-workspace/.active_repo
                    chown concerto:concerto /opt/concerto-workspace/.active_repo 2>/dev/null || true
                fi

                # Mark first run if needed (must happen AFTER clone succeeds, so the
                # welcome message is delivered alongside a ready workspace).
                if [ "$NEEDS_FIRST_RUN" = "1" ] && [ -n "$GITHUB_LOGIN" ] && [ -d "$CLONE_DIR/.git" ]; then
                    printf '%s\n' "$GITHUB_LOGIN" > "$FIRST_RUN_FILE"
                    chmod 644 "$FIRST_RUN_FILE"
                    chown concerto:concerto "$FIRST_RUN_FILE" 2>/dev/null || true
                fi
            fi
            sleep 30
        done
    ) &
    echo "[entrypoint] Git-creds polling started (every 30s)"
fi

echo "[entrypoint] All services started. Container ready."
echo "[entrypoint] Waiting on MCP server (PID $MCP_PID)..."
wait $MCP_PID
