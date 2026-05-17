#!/usr/bin/env bash
# Concerto installer dry-run — renders cloud_init.yaml.j2 with fake values
# and validates the result without touching systemd or installing packages.
#
# Usage:
#   ./installer/test/dry_run.sh            # full dry-run
#   ./installer/test/dry_run.sh --check-sync  # only verify mcp_server.py is in sync
#
# Requirements on host: python3, pip (jinja2 + pyyaml auto-installed in venv)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_DIR="$(mktemp -d /tmp/concerto-dryrun-XXXXXX)"
trap 'rm -rf "${WORK_DIR}"' EXIT

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; FAILED=$((FAILED+1)); }
info() { echo -e "${YELLOW}[INFO]${NC} $*"; }

FAILED=0

# ─── --check-sync: verify installer/mcp_server.py matches the embedded copy ──

if [[ "${1:-}" == "--check-sync" ]]; then
  info "Checking mcp_server.py sync between standalone file and cloud_init.yaml.j2..."

  # Extract the embedded mcp_server.py from the YAML using Python
  # Need jinja2+pyyaml — install to a temp venv if not present
  _SYNC_VENV="$(mktemp -d /tmp/concerto-sync-venv-XXXXXX)"
  trap 'rm -rf "${_SYNC_VENV}"' EXIT
  python3 -m venv "${_SYNC_VENV}" >/dev/null 2>&1
  "${_SYNC_VENV}/bin/pip" install --quiet jinja2 pyyaml >/dev/null 2>&1

  "${_SYNC_VENV}/bin/python3" - <<'PYEOF'
import sys, yaml, pathlib, difflib
from jinja2 import Environment, FileSystemLoader

# Render with dummy values so the template is valid YAML
env = Environment(loader=FileSystemLoader("installer"), keep_trailing_newline=True)
tmpl = env.get_template("cloud_init.yaml.j2")
rendered = tmpl.render(
    concerto_token="x", concerto_callback_url="https://x.example.com/cb",
    ssh_authorized_key="ssh-ed25519 AAAA fake@host", customer_email="x@x.com",
)

doc = yaml.safe_load(rendered)
wf = {e["path"]: e for e in doc.get("write_files", []) if isinstance(e, dict) and "path" in e}
key = "/opt/concerto/mcp_server.py"
if key not in wf:
    print(f"ERROR: {key} not found in write_files"); sys.exit(1)

embedded = wf[key].get("content", "").rstrip()
standalone = pathlib.Path("installer/mcp_server.py").read_text().rstrip()

if embedded == standalone:
    print("SYNC OK: mcp_server.py matches embedded version in cloud_init.yaml.j2")
    sys.exit(0)
else:
    diff = list(difflib.unified_diff(
        standalone.splitlines(), embedded.splitlines(),
        fromfile="installer/mcp_server.py", tofile="cloud_init embedded", lineterm=""
    ))
    print("SYNC FAIL: files differ")
    print("\n".join(diff[:40]))
    sys.exit(1)
PYEOF
  exit $?
fi

# ─── Full dry-run ──────────────────────────────────────────────────────────────

info "Working in ${WORK_DIR}"
info "Installer dir: ${INSTALLER_DIR}"

# ── Step 1: bootstrap Jinja2 + PyYAML in a throwaway venv ────────────────────

info "Step 1: Installing Jinja2 + PyYAML..."
python3 -m venv "${WORK_DIR}/venv"
"${WORK_DIR}/venv/bin/pip" install --quiet jinja2 pyyaml
pass "Jinja2 + PyYAML ready"

# ── Step 2: Render the Jinja2 template with fake values ─────────────────────

info "Step 2: Rendering cloud_init.yaml.j2 with fake values..."
RENDERED="${WORK_DIR}/rendered.yaml"

"${WORK_DIR}/venv/bin/python3" - <<PYEOF
import sys
sys.path.insert(0, "")
from jinja2 import Environment, FileSystemLoader, StrictUndefined

env = Environment(
    loader=FileSystemLoader("${INSTALLER_DIR}"),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)
tmpl = env.get_template("cloud_init.yaml.j2")
out = tmpl.render(
    concerto_token="dryrun_token_abc123",
    concerto_callback_url="https://empire.example.com/api/concerto/callback",
    ssh_authorized_key="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKeyForDryRunOnly dryrun@concerto",
    customer_email="dryrun@example.com",
)
with open("${RENDERED}", "w") as f:
    f.write(out)
print(f"Rendered: ${RENDERED}")
PYEOF
pass "Template rendered → ${RENDERED}"

# ── Step 3: YAML parse validation ────────────────────────────────────────────

info "Step 3: Validating YAML structure..."
"${WORK_DIR}/venv/bin/python3" - <<PYEOF
import sys, yaml

with open("${RENDERED}") as f:
    doc = yaml.safe_load(f)

errors = []
if not isinstance(doc, dict):
    errors.append("top-level must be a YAML mapping")

# cloud-config required sections
for key in ("ssh_authorized_keys", "write_files", "runcmd"):
    if key not in doc:
        errors.append(f"missing required key: {key}")

if "write_files" in doc:
    paths = [e.get("path") for e in doc["write_files"] if isinstance(e, dict)]
    required_paths = [
        "/etc/concerto/env",
        "/etc/concerto/version",
        "/opt/concerto/mcp_server.py",
        "/etc/nginx/conf.d/concerto.conf",
        "/etc/systemd/system/concerto-mcp.service",
        "/etc/systemd/system/concerto-tunnel.service",
        "/etc/systemd/system/concerto-ttyd.service",
        "/opt/concerto/provision_complete.sh",
    ]
    for p in required_paths:
        if p not in paths:
            errors.append(f"write_files missing path: {p}")

if "runcmd" in doc:
    if not isinstance(doc["runcmd"], list) or len(doc["runcmd"]) == 0:
        errors.append("runcmd must be a non-empty list")

if "ssh_authorized_keys" in doc:
    keys = doc["ssh_authorized_keys"]
    if not isinstance(keys, list) or len(keys) == 0:
        errors.append("ssh_authorized_keys must be a non-empty list")
    elif "dryrun_token_abc123" in str(keys[0]):
        pass  # template var would have been substituted; fine
    elif not str(keys[0]).startswith("ssh-"):
        errors.append(f"ssh_authorized_keys[0] looks wrong: {keys[0][:60]}")

if errors:
    for e in errors:
        print(f"  ERROR: {e}")
    sys.exit(1)
else:
    print(f"  OK: {len(doc.get('write_files', []))} write_files, {len(doc.get('runcmd', []))} runcmd steps")
PYEOF
pass "YAML structure valid"

# ── Step 4: cloud-init schema check (if cloud-init is installed) ─────────────

info "Step 4: cloud-init schema check..."
if command -v cloud-init &>/dev/null; then
  if cloud-init schema --config-file "${RENDERED}" 2>&1; then
    pass "cloud-init schema validates"
  else
    fail "cloud-init schema validation failed"
  fi
else
  info "cloud-init not installed — skipping schema check (install cloud-init to enable)"
fi

# ── Step 5: Extract and validate embedded mcp_server.py ─────────────────────

info "Step 5: Validating embedded mcp_server.py (Python syntax + imports)..."
MCP_PY="${WORK_DIR}/extracted_mcp_server.py"

"${WORK_DIR}/venv/bin/python3" - <<PYEOF
import sys, yaml, pathlib

rendered = pathlib.Path("${RENDERED}").read_text()
doc = yaml.safe_load(rendered)
wf = {e["path"]: e for e in doc.get("write_files", []) if isinstance(e, dict) and "path" in e}
key = "/opt/concerto/mcp_server.py"
if key not in wf:
    print(f"  ERROR: {key} not found in write_files")
    sys.exit(1)

content = wf[key].get("content", "")
pathlib.Path("${MCP_PY}").write_text(content)
print(f"  Extracted {len(content.splitlines())} lines")
PYEOF

# Syntax check (py_compile)
python3 -m py_compile "${MCP_PY}" && pass "mcp_server.py syntax OK" || fail "mcp_server.py syntax error"

# Check key identifiers
for symbol in start_claude_session list_claude_sessions get_claude_session kill_claude_session BearerAuth anyio; do
  if grep -q "${symbol}" "${MCP_PY}"; then
    pass "  symbol present: ${symbol}"
  else
    fail "  symbol missing: ${symbol}"
  fi
done

# ── Step 6: Validate standalone mcp_server.py syntax ─────────────────────────

info "Step 6: Validating standalone installer/mcp_server.py..."
python3 -m py_compile "${INSTALLER_DIR}/mcp_server.py" && pass "standalone mcp_server.py syntax OK" || fail "standalone mcp_server.py syntax error"

# ── Step 7: Simulate safe runcmd steps ───────────────────────────────────────

info "Step 7: Simulating safe runcmd steps (NO systemd, NO apt, NO npm)..."

# Check all expected commands appear in rendered runcmd
"${WORK_DIR}/venv/bin/python3" - <<PYEOF
import yaml, sys

with open("${RENDERED}") as f:
    doc = yaml.safe_load(f)

runcmd = doc.get("runcmd", [])
runcmd_text = str(runcmd)

required_patterns = [
    "nodesource.com/setup_20.x",
    "@anthropic-ai/claude-code",
    "cloudflared-linux-amd64.deb",
    "mcp[cli]",
    "openssl rand -hex 32",
    "provision_complete.sh",
    "concerto-mcp",
    "concerto-ttyd",
    "concerto-tunnel",
]

ok = True
for p in required_patterns:
    if p in runcmd_text:
        print(f"  found: {p}")
    else:
        print(f"  MISSING: {p}")
        ok = False

sys.exit(0 if ok else 1)
PYEOF
pass "runcmd contains all required steps"

# ── Summary ───────────────────────────────────────────────────────────────────

echo
if [ "${FAILED}" -eq 0 ]; then
  pass "All checks passed. Rendered YAML: ${RENDERED}"
else
  fail "${FAILED} check(s) failed."
  exit 1
fi
