#!/usr/bin/env bash
set -euo pipefail

# --- pre-flight: cloud-init must be pure ASCII and embedded mcp_server.py in
#     sync. A stray non-ASCII byte (e.g. an em-dash in a docstring) makes
#     cloud-init reject the ENTIRE config -> fresh droplets come up empty.
#     This check makes that failure mode impossible to ship silently.
REPO_PRE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$REPO_PRE" <<'PYGUARD'
import sys, hashlib
root = sys.argv[1]
ci = root + "/installer/cloud_init.yaml.j2"
canon = root + "/installer/mcp_server.py"
raw = open(ci, "rb").read()
bad = [(i, b) for i, b in enumerate(raw) if b >= 0x80]
if bad:
    i, b = bad[0]
    print(f"[deploy] FATAL: non-ASCII byte 0x{b:02x} at offset {i} in cloud_init.yaml.j2")
    print(f"         context: {raw[max(0,i-40):i+40]!r}")
    print("         cloud-init would reject the whole config -> empty droplets. Aborting.")
    sys.exit(1)
# embedded copy must equal canonical mcp_server.py
lines = open(ci, encoding="utf-8").read().split("\n")
pi = next(i for i, l in enumerate(lines) if l.strip().startswith("- path: /opt/concerto/mcp_server.py"))
cidx = next(i for i in range(pi, pi + 8) if lines[i].strip() == "content: |")
start = cidx + 1
end = next(i for i in range(start, len(lines)) if lines[i].startswith("  - path:") or lines[i].startswith("  # -- "))
ded = "\n".join((l[6:] if len(l) >= 6 else l) for l in lines[start:end]).rstrip("\n") + "\n"
cn = open(canon, encoding="utf-8").read().rstrip("\n") + "\n"
if ded != cn:
    print("[deploy] FATAL: embedded /opt/concerto/mcp_server.py in cloud_init.yaml.j2")
    print("         differs from installer/mcp_server.py. Regenerate before deploying.")
    sys.exit(1)
print(f"[deploy] pre-flight OK: cloud-init pure ASCII, embedded mcp_server.py in sync (sha {hashlib.sha256(cn.encode()).hexdigest()[:12]})")
PYGUARD

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/concerto/backend"
INSTALLER_DIR="/opt/concerto/installer"
DB_DIR="/var/lib/concerto"
KEYS_DIR="$DB_DIR/keys"
SERVICE_SRC="$REPO_ROOT/deploy/concerto-backend.service"
SERVICE_DST="/etc/systemd/system/concerto-backend.service"
CF_CONFIG="/etc/cloudflared/config.yml"

echo "==> [concerto] Installing backend to $INSTALL_DIR"

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

echo "==> [concerto] Creating/updating Python venv"
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    python3 -m venv "$INSTALL_DIR/.venv"
fi
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

echo "==> [concerto] Installing systemd service"
cp "$SERVICE_SRC" "$SERVICE_DST"
systemctl daemon-reload
systemctl reset-failed concerto-backend.service 2>/dev/null || true
systemctl enable concerto-backend.service
systemctl restart concerto-backend.service

echo "==> [concerto] Configuring cloudflared"
if [ -f "$CF_CONFIG" ]; then
    if ! grep -q "api.concerto.run" "$CF_CONFIG"; then
        python3 - "$CF_CONFIG" <<'PYEOF'
import sys
path = sys.argv[1]
content = open(path).read()
catch_all = "  - service: http_status:404"
new_rule = "  - hostname: api.concerto.run\n    service: http://127.0.0.1:8090\n"
if catch_all in content and "api.concerto.run" not in content:
    content = content.replace(catch_all, new_rule + catch_all)
    open(path, "w").write(content)
    print("[concerto] Inserted api.concerto.run into cloudflared ingress")
else:
    print("[concerto] cloudflared config unchanged")
PYEOF
        systemctl reload cloudflared 2>/dev/null || systemctl restart cloudflared
    else
        echo "[concerto] api.concerto.run already present in cloudflared config"
    fi
else
    echo "[concerto] WARNING: $CF_CONFIG not found — cloudflared not configured"
fi

echo "==> [concerto] Service status"
systemctl status concerto-backend.service --no-pager -l || true

echo "==> [concerto] Smoke test"
sleep 2
curl -sf http://127.0.0.1:8090/healthz && echo "" || echo "[concerto] WARNING: healthz not yet responding"
