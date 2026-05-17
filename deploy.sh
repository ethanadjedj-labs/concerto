#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/maestro/backend"
INSTALLER_DIR="/opt/maestro/installer"
DB_DIR="/var/lib/maestro"
KEYS_DIR="$DB_DIR/keys"
SERVICE_SRC="$REPO_ROOT/deploy/maestro-backend.service"
SERVICE_DST="/etc/systemd/system/maestro-backend.service"
CF_CONFIG="/etc/cloudflared/config.yml"

echo "==> [maestro] Installing backend to $INSTALL_DIR"

mkdir -p "$INSTALL_DIR" "$DB_DIR" "$KEYS_DIR"
chmod 700 "$KEYS_DIR"

rsync -av --delete \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$REPO_ROOT/backend/" "$INSTALL_DIR/"

if [ -d "$REPO_ROOT/installer" ]; then
    mkdir -p "$INSTALLER_DIR"
    rsync -av "$REPO_ROOT/installer/" "$INSTALLER_DIR/"
fi

echo "==> [maestro] Creating/updating Python venv"
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    python3 -m venv "$INSTALL_DIR/.venv"
fi
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

echo "==> [maestro] Installing systemd service"
cp "$SERVICE_SRC" "$SERVICE_DST"
systemctl daemon-reload
systemctl reset-failed maestro-backend.service 2>/dev/null || true
systemctl enable maestro-backend.service
systemctl restart maestro-backend.service

echo "==> [maestro] Configuring cloudflared"
if [ -f "$CF_CONFIG" ]; then
    if ! grep -q "api.maestro.run" "$CF_CONFIG"; then
        python3 - "$CF_CONFIG" <<'PYEOF'
import sys
path = sys.argv[1]
content = open(path).read()
catch_all = "  - service: http_status:404"
new_rule = "  - hostname: api.maestro.run\n    service: http://127.0.0.1:8090\n"
if catch_all in content and "api.maestro.run" not in content:
    content = content.replace(catch_all, new_rule + catch_all)
    open(path, "w").write(content)
    print("[maestro] Inserted api.maestro.run into cloudflared ingress")
else:
    print("[maestro] cloudflared config unchanged")
PYEOF
        systemctl reload cloudflared 2>/dev/null || systemctl restart cloudflared
    else
        echo "[maestro] api.maestro.run already present in cloudflared config"
    fi
else
    echo "[maestro] WARNING: $CF_CONFIG not found — cloudflared not configured"
fi

echo "==> [maestro] Service status"
systemctl status maestro-backend.service --no-pager -l || true

echo "==> [maestro] Smoke test"
sleep 2
curl -sf http://127.0.0.1:8090/healthz && echo "" || echo "[maestro] WARNING: healthz not yet responding"
