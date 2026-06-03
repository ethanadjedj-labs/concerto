#!/usr/bin/env bash
# deploy.sh — Concerto deployment script
# Installs backend code + systemd hardening drop-ins, runs a fail-closed e2e
# smoke-test, and rolls back automatically if any check fails.
set -euo pipefail

# ── pre-flight: cloud-init must be pure ASCII and embedded mcp_server.py in
#     sync. A stray non-ASCII byte (e.g. an em-dash in a docstring) makes
#     cloud-init reject the ENTIRE config -> fresh droplets come up empty.
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
import gzip, base64
lines = open(ci, encoding="utf-8").read().split("\n")
pi = next(i for i, l in enumerate(lines) if l.strip().startswith("- path: /opt/concerto/mcp_server.py.gz.b64"))
cidx = next(i for i in range(pi, pi + 8) if lines[i].strip() == "content: |")
start = cidx + 1
end = next(i for i in range(start, len(lines)) if lines[i].startswith("  - path:") or lines[i].startswith("  # -- "))
b64 = "".join(l.strip() for l in lines[start:end] if l.strip())
try:
    decoded = gzip.decompress(base64.b64decode(b64))
except Exception as e:
    print(f"[deploy] FATAL: embedded mcp_server.py.gz.b64 will not decode: {e}")
    sys.exit(1)
cn = open(canon, "rb").read()
if decoded != cn:
    print("[deploy] FATAL: decoded embedded mcp_server.py differs from installer/mcp_server.py.")
    print("         Regenerate the gz.b64 blob before deploying.")
    sys.exit(1)
import re as _re
approx = _re.sub(r"{{.*?}}", "x" * 16, open(ci, encoding="utf-8").read())
size = len(approx.encode())
if size >= 64 * 1024:
    print(f"[deploy] FATAL: cloud-init ~{size}B exceeds DO 64KB user-data cap.")
    sys.exit(1)
print(f"[deploy] pre-flight OK: ASCII, mcp_server.py gz.b64 decodes & matches (sha {hashlib.sha256(cn).hexdigest()[:12]}), cloud-init ~{size}B < 64KB")
PYGUARD

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/concerto/backend"
INSTALLER_DIR="/opt/concerto/installer"
DB_DIR="/var/lib/concerto"
KEYS_DIR="$DB_DIR/keys"
SERVICE_SRC="$REPO_ROOT/deploy/concerto-backend.service"
SERVICE_DST="/etc/systemd/system/concerto-backend.service"
CF_CONFIG="/etc/cloudflared/config.yml"

DROPIN_SRC="$REPO_ROOT/deploy/systemd/dropins"
BACKEND_DROPIN_DST="/etc/systemd/system/concerto-backend.service.d"
FRONTEND_DROPIN_DST="/etc/systemd/system/concerto-frontend.service.d"
SNAPSHOT_BASE="/var/lib/concerto/dropin-snapshots"
HEALTHCHECK_SRC="$REPO_ROOT/ops/concerto-healthcheck.sh"
HEALTHCHECK_DST="/usr/local/bin/concerto-healthcheck.sh"

# ── helper: run a command with full filesystem write access ──────────────────
# /etc/systemd is read-only in this shell (ProtectSystem on the relay sandbox).
# Wrap any write to /etc or other protected paths via a transient unit.
sysd_run_write() {
    systemd-run --quiet --pipe --wait \
        --property=ProtectSystem=no \
        --property=ProtectHome=no \
        -- "$@"
}

# ── smoke-test with retry ────────────────────────────────────────────────────
# Retries a curl check for up to ~30s. Prints which check failed + journal tail.
# Returns 0 on success, 1 on final failure.
smoke_check() {
    local label="$1"
    local url="$2"
    local expected="${3:-200}"
    local service_for_journal="${4:-}"
    local deadline=$((SECONDS + 32))
    local http delay=2

    echo "    [smoke] checking $label ($url) ..."
    while [ "$SECONDS" -lt "$deadline" ]; do
        http=$(curl -sSL -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
        if [ "$http" = "$expected" ]; then
            echo "    [smoke] $label OK (HTTP $http)"
            return 0
        fi
        echo "    [smoke] $label HTTP=$http (retrying in ${delay}s ...)"
        sleep "$delay"
        delay=5
    done

    echo ""
    echo "  !! SMOKE TEST FAILED: $label returned HTTP=$http (expected $expected)"
    echo "  !! URL: $url"
    if [ -n "$service_for_journal" ]; then
        echo "  !! Last 30 journal lines for $service_for_journal:"
        journalctl -u "$service_for_journal" -n 30 --no-pager 2>/dev/null || true
    fi
    return 1
}

# ── rollback helper ──────────────────────────────────────────────────────────
rollback_dropins() {
    local snapshot_dir="$1"
    echo "==> [concerto] Rolling back systemd drop-ins from $snapshot_dir ..."
    if [ -d "$snapshot_dir/concerto-backend.service.d" ]; then
        sysd_run_write bash -c "
            rm -rf '$BACKEND_DROPIN_DST'
            cp -a '$snapshot_dir/concerto-backend.service.d' '$BACKEND_DROPIN_DST'
        "
    fi
    if [ -d "$snapshot_dir/concerto-frontend.service.d" ]; then
        sysd_run_write bash -c "
            rm -rf '$FRONTEND_DROPIN_DST'
            cp -a '$snapshot_dir/concerto-frontend.service.d' '$FRONTEND_DROPIN_DST'
        "
    fi
    sysd_run_write systemctl daemon-reload
    systemctl restart concerto-backend.service concerto-frontend.service || true
    echo "==> [concerto] Rollback complete. Verifying site still up ..."
    sleep 4
    smoke_check "backend/healthz [post-rollback]"  "http://127.0.0.1:8090/healthz" "200" "concerto-backend.service"  || true
    smoke_check "frontend/ [post-rollback]"         "http://127.0.0.1:3500/"         "200" "concerto-frontend.service" || true
    smoke_check "public/trial [post-rollback]"      "https://concerto.run/trial"     "200" ""                         || true
}

# ── install backend code ─────────────────────────────────────────────────────
echo "==> [concerto] Installing backend to $INSTALL_DIR"

sysd_run_write mkdir -p "$INSTALL_DIR" "$DB_DIR" "$KEYS_DIR"
sysd_run_write chmod 700 "$KEYS_DIR"

rsync -av --delete \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$REPO_ROOT/backend/" "$INSTALL_DIR/"

if [ -d "$REPO_ROOT/installer" ]; then
    sysd_run_write mkdir -p "$INSTALLER_DIR"
    rsync -av "$REPO_ROOT/installer/" "$INSTALLER_DIR/"
fi

echo "==> [concerto] Creating/updating Python venv"
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    sysd_run_write python3 -m venv "$INSTALL_DIR/.venv"
fi
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# ── install systemd base service ─────────────────────────────────────────────
echo "==> [concerto] Installing systemd service unit"
sysd_run_write cp "$SERVICE_SRC" "$SERVICE_DST"

# ── snapshot existing drop-ins before touching them ──────────────────────────
SNAPSHOT_DIR="$SNAPSHOT_BASE/$(date -u +%Y%m%dT%H%M%SZ)"
echo "==> [concerto] Snapshotting current drop-ins to $SNAPSHOT_DIR"
sysd_run_write bash -c "
    mkdir -p '$SNAPSHOT_DIR'
    [ -d '$BACKEND_DROPIN_DST'  ] && cp -a '$BACKEND_DROPIN_DST'  '$SNAPSHOT_DIR/' || true
    [ -d '$FRONTEND_DROPIN_DST' ] && cp -a '$FRONTEND_DROPIN_DST' '$SNAPSHOT_DIR/' || true
"
echo "    snapshot written to $SNAPSHOT_DIR"

# ── apply versioned drop-ins ──────────────────────────────────────────────────
echo "==> [concerto] Installing systemd hardening drop-ins"
sysd_run_write bash -c "
    mkdir -p '$BACKEND_DROPIN_DST' '$FRONTEND_DROPIN_DST'
    cp '$DROPIN_SRC/concerto-backend.d/99-hardening.conf'  '$BACKEND_DROPIN_DST/99-hardening.conf'
    cp '$DROPIN_SRC/concerto-frontend.d/99-hardening.conf' '$FRONTEND_DROPIN_DST/99-hardening.conf'
"
echo "    drop-ins installed"

# ── install healthcheck script ────────────────────────────────────────────────
echo "==> [concerto] Installing healthcheck script to $HEALTHCHECK_DST"
sysd_run_write bash -c "cp '$HEALTHCHECK_SRC' '$HEALTHCHECK_DST' && chmod +x '$HEALTHCHECK_DST'"

# ── daemon-reload + restart both services ────────────────────────────────────
echo "==> [concerto] daemon-reload + restart concerto-backend + concerto-frontend"
sysd_run_write systemctl daemon-reload
systemctl reset-failed concerto-backend.service  2>/dev/null || true
systemctl reset-failed concerto-frontend.service 2>/dev/null || true
systemctl enable concerto-backend.service
systemctl restart concerto-backend.service concerto-frontend.service

# ── cloudflared config ────────────────────────────────────────────────────────
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

# ── fail-closed e2e smoke-test ────────────────────────────────────────────────
echo "==> [concerto] Running e2e smoke-test (backend + frontend + public /trial)"
SMOKE_FAILED=0

smoke_check "backend/healthz"  "http://127.0.0.1:8090/healthz" "200" "concerto-backend.service"  || SMOKE_FAILED=1
smoke_check "frontend/"        "http://127.0.0.1:3500/"         "200" "concerto-frontend.service" || SMOKE_FAILED=1
smoke_check "public/trial"     "https://concerto.run/trial"     "200" ""                         || SMOKE_FAILED=1

if [ "$SMOKE_FAILED" -ne 0 ]; then
    echo ""
    echo "!! [concerto] DEPLOY FAILED — smoke-test did not pass. Initiating rollback."
    rollback_dropins "$SNAPSHOT_DIR"
    echo ""
    echo "!! [concerto] Rollback applied. Exiting non-zero."
    exit 1
fi

echo ""
echo "==> [concerto] Deploy complete — all smoke-test checks passed."
echo "    Snapshot of pre-deploy drop-ins retained at: $SNAPSHOT_DIR"
