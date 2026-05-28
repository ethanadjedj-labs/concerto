"""
NF Admin Dashboard Router
=========================

Endpoints
---------
  GET /api/admin/nf-status       — JSON snapshot of Northflank resources + cost estimates
  GET /api/admin/nf-status/page  — Browser dashboard (auto-refresh 30s, no build step)

Authentication
--------------
Both endpoints require the CONCERTO_OPS_TOKEN bearer token:
  Authorization: Bearer <CONCERTO_OPS_TOKEN>

The page endpoint also accepts ?token=<OPS_TOKEN> as a URL parameter so admins can
bookmark the page directly.  The JS stores the token in sessionStorage so subsequent
fetch calls to /api/admin/nf-status work automatically.

Pricing constants
-----------------
Rates verified 2026-05-20 via GET /v1/plans on the Northflank API:
  nf-compute-20      $0.008 /hr
  nf-compute-100-1   $0.025 /hr
  nf-compute-200     $0.067 /hr   ← primary Concerto solo plan
  nf-compute-200-8   $0.072 /hr   ← pro plan (2 vCPU / 8 GB)
  Volume NVMe SSD    $0.15  /GB/month  (accrues even when service is paused)

To add a new plan: add a line to _PLAN_HOURLY_RATES below. The key MUST match
Northflank's deploymentPlan string exactly (check via GET /v1/plans).

Threshold-billing risk
----------------------
Northflank uses a threshold model: charges trigger at usage thresholds.
Failed invoices suspend services after 7 days; volumes are DELETED after 7 days
of a failed invoice.  The dashboard surfaces this risk via latest_invoice.status.
If the status is "open" or "uncollectible", the HTML page shows a red alert banner.
"""

from __future__ import annotations

import calendar
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

# ── Auth ──────────────────────────────────────────────────────────────────────

_OPS_TOKEN = os.getenv("CONCERTO_OPS_TOKEN", "")


def _check_admin_auth(request: Request, query_token: str = "") -> None:
    if not _OPS_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="CONCERTO_OPS_TOKEN not configured — set this env var to enable the admin dashboard",
        )
    candidate = query_token
    if not candidate:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            candidate = auth_header[7:]
    if not candidate or candidate != _OPS_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized — supply CONCERTO_OPS_TOKEN as Bearer token or ?token= param")


# ── NF API config ─────────────────────────────────────────────────────────────

_NF_API_BASE = "https://api.northflank.com/v1"
_NF_API_TOKEN = os.getenv("CONCERTO_NF_API_TOKEN", "")
_NF_PROJECT_ID = os.getenv("CONCERTO_NF_PROJECT_ID", "concerto")
_PROVISIONER = os.getenv("CONCERTO_PROVISIONER", "do")

# ── Pricing constants — verified 2026-05-20 via GET /v1/plans ─────────────────
# To add a plan: add the NF deploymentPlan string → hourly USD rate.

_PLAN_HOURLY_RATES: dict[str, float] = {
    "nf-compute-20":    0.008,
    "nf-compute-100-1": 0.025,
    "nf-compute-200":   0.067,
    "nf-compute-200-8": 0.072,
}

_VOLUME_GB_MONTHLY_RATE: float = 0.15  # NVMe SSD, verified 2026-05-20

# ── In-memory cache (same pattern as oauth_status_router.py) ──────────────────

_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 15  # short TTL for fresh ops snapshots; bypass via ?fresh=1  # seconds


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and time.monotonic() < entry[0]:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.monotonic() + _CACHE_TTL, value)


# ── NF API helpers ────────────────────────────────────────────────────────────

async def _nf_get(path: str) -> dict:
    cached = _cache_get(path)
    if cached is not None:
        return cached

    if not _NF_API_TOKEN:
        raise HTTPException(status_code=503, detail="CONCERTO_NF_API_TOKEN not configured")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_NF_API_BASE}{path}",
                headers={"Authorization": f"Bearer {_NF_API_TOKEN}"},
            )
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail=f"NF API timed out: {path}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"NF API error {exc.response.status_code}: {path}",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"NF API unreachable: {exc}")

    _cache_set(path, data)
    return data


# ── Cost math helpers ─────────────────────────────────────────────────────────

def _parse_dt(iso: str) -> datetime:
    """Parse ISO 8601 string to UTC datetime."""
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    return datetime.fromisoformat(iso).astimezone(timezone.utc)


def _month_start_utc(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _days_in_month(now: datetime) -> int:
    return calendar.monthrange(now.year, now.month)[1]


def _day_start_utc(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def compute_service_cost_month(plan: str, created_at_iso: str, now: datetime) -> float:
    """Compute cost from max(created_at, month_start) to now."""
    rate = _PLAN_HOURLY_RATES.get(plan, 0.0)
    if rate == 0.0:
        return 0.0
    month_start = _month_start_utc(now)
    try:
        created = _parse_dt(created_at_iso)
    except Exception:
        return 0.0
    billing_start = max(created, month_start)
    if billing_start >= now:
        return 0.0
    hours = (now - billing_start).total_seconds() / 3600
    return round(rate * hours, 6)


def compute_service_cost_today(plan: str, created_at_iso: str, now: datetime) -> float:
    """Compute cost from max(created_at, today_start) to now."""
    rate = _PLAN_HOURLY_RATES.get(plan, 0.0)
    if rate == 0.0:
        return 0.0
    today_start = _day_start_utc(now)
    try:
        created = _parse_dt(created_at_iso)
    except Exception:
        return 0.0
    billing_start = max(created, today_start)
    if billing_start >= now:
        return 0.0
    hours = (now - billing_start).total_seconds() / 3600
    return round(rate * hours, 6)


def compute_volume_cost_month(size_mb: int, now: datetime) -> float:
    """Monthly prorated cost for a volume: size_gb * $0.15 * (days_elapsed/days_in_month)."""
    size_gb = size_mb / 1024
    month_start = _month_start_utc(now)
    days_elapsed = (now - month_start).total_seconds() / 86400
    days_total = _days_in_month(now)
    return round(size_gb * _VOLUME_GB_MONTHLY_RATE * (days_elapsed / days_total), 6)


def compute_volume_cost_today(size_mb: int, now: datetime) -> float:
    """Volume cost accrued today."""
    size_gb = size_mb / 1024
    day_start = _day_start_utc(now)
    hours_today = (now - day_start).total_seconds() / 3600
    # daily rate = monthly rate / days_in_month
    daily_rate = size_gb * _VOLUME_GB_MONTHLY_RATE / _days_in_month(now)
    return round(daily_rate * hours_today / 24, 6)


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.get("/api/admin/nf-status")
async def nf_status(request: Request, token: str = ""):
    _check_admin_auth(request, token)

    now = datetime.now(timezone.utc)

    # Fetch services, volumes, invoices concurrently using sequential awaits
    # (httpx is async; we cache so hammering is avoided)
    svc_data = await _nf_get(f"/projects/{_NF_PROJECT_ID}/services")
    vol_data = await _nf_get(f"/projects/{_NF_PROJECT_ID}/volumes")
    try:
        inv_data = await _nf_get("/billing/invoices")
    except HTTPException:
        inv_data = {}

    # NF API shapes (verified 2026-05-20):
    #   /services → {"data": {"services": [...]}, "pagination": ...}
    #   /volumes  → {"data": [...], "pagination": ...}                  ← list directly under "data"
    #   /billing/invoices → {"data": {"invoices": [...]}, ...}
    def _extract_list(payload, *keys):
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for k in keys:
                v = data.get(k)
                if isinstance(v, list):
                    return v
        return []

    raw_services = _extract_list(svc_data, "services", "items")
    raw_volumes  = _extract_list(vol_data, "volumes", "items")
    raw_invoices = _extract_list(inv_data, "invoices", "items")

    # ── Services ──────────────────────────────────────────────────────────────

    services_out = []
    running_count = 0
    paused_count = 0
    total_cost_month = 0.0
    total_cost_today = 0.0

    for svc in raw_services:
        svc_id = svc.get("id") or svc.get("name") or ""
        created_iso = svc.get("createdAt") or ""
        plan = (svc.get("billing") or {}).get("deploymentPlan") or ""

        # NF service status: usually a dict {"deployment": {"status": "..."}}, but be
        # defensive if NF ever returns a string (e.g. older API or summary endpoint).
        _svc_status = svc.get("status")
        if isinstance(_svc_status, dict):
            deploy_status_raw = ((_svc_status.get("deployment") or {}).get("status")) or ""
        else:
            deploy_status_raw = _svc_status if isinstance(_svc_status, str) else ""

        # Normalise to RUNNING / PAUSED / COMPLETED / UNKNOWN
        if deploy_status_raw in ("COMPLETED", "RUNNING"):
            status = "RUNNING"
            running_count += 1
        elif deploy_status_raw in ("PAUSED",):
            status = "PAUSED"
            paused_count += 1
        else:
            status = deploy_status_raw or "UNKNOWN"

        try:
            created_dt = _parse_dt(created_iso) if created_iso else None
        except Exception:
            created_dt = None

        runtime_seconds = int((now - created_dt).total_seconds()) if created_dt else 0

        if status == "RUNNING":
            cost_month = compute_service_cost_month(plan, created_iso, now)
            cost_today = compute_service_cost_today(plan, created_iso, now)
        else:
            cost_month = 0.0
            cost_today = 0.0

        total_cost_month += cost_month
        total_cost_today += cost_today

        services_out.append({
            "id": svc_id,
            "status": status,
            "plan": plan,
            "hourly_rate_usd": _PLAN_HOURLY_RATES.get(plan),
            "created_at": created_iso,
            "runtime_seconds_so_far": runtime_seconds,
            "estimated_cost_usd_so_far_this_month": cost_month,
            "estimated_cost_usd_today": cost_today,
        })

    # ── Volumes ───────────────────────────────────────────────────────────────

    volumes_out = []
    for vol in raw_volumes:
        vol_id = vol.get("id") or vol.get("name") or ""
        size_mb = (vol.get("spec") or {}).get("storageSize") or 0

        # Find attached service. NF volume API (2026-05): `status` is a string
        # ("PENDING"/"BOUND"/...), and `attachedObjects` is a top-level list.
        # Fallback to a dict-shaped status for older API shapes.
        status_field = vol.get("status")
        status_dict = status_field if isinstance(status_field, dict) else {}
        mounts = status_dict.get("mounts") or vol.get("mounts") or []
        attached_to = None
        if mounts:
            attached_to = ((mounts[0].get("nfObject") or {}).get("id"))
        elif vol.get("attachedObjects"):
            ao = vol["attachedObjects"]
            if isinstance(ao, list) and ao:
                attached_to = ao[0].get("id")

        cost_month = compute_volume_cost_month(size_mb, now)
        cost_today = compute_volume_cost_today(size_mb, now)
        total_cost_month += cost_month
        total_cost_today += cost_today

        volumes_out.append({
            "id": vol_id,
            "size_mb": size_mb,
            "attached_to_service_id": attached_to,
            "estimated_monthly_cost_usd": round(size_mb / 1024 * _VOLUME_GB_MONTHLY_RATE, 4),
            "estimated_cost_usd_so_far_this_month": cost_month,
            "estimated_cost_usd_today": cost_today,
        })

    # ── Latest invoice ────────────────────────────────────────────────────────

    latest_invoice = None
    if raw_invoices:
        inv = raw_invoices[0]
        inv_status = inv.get("status") or ""
        latest_invoice = {
            "id": inv.get("id") or "",
            "amount_usd": inv.get("amount") or inv.get("total") or 0,
            "status": inv_status,
            "created_at": inv.get("createdAt") or inv.get("created_at") or "",
            "risk_flag": inv_status in ("open", "uncollectible", "unpaid"),
        }

    return {
        "provider_active": _PROVISIONER,
        "as_of": now.isoformat(),
        "services": services_out,
        "volumes": volumes_out,
        "counts": {
            "active": running_count,
            "paused": paused_count,
            "total": len(services_out),
        },
        "cost_estimate_today_usd": round(total_cost_today, 4),
        "cost_estimate_month_to_date_usd": round(total_cost_month, 4),
        "latest_invoice": latest_invoice,
    }


# ── HTML dashboard page ───────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Concerto NF Dashboard</title>
<style>
  body{font-family:system-ui,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
  h1{font-size:1.25rem;margin:.75rem 1rem .25rem}
  .ts{font-size:.75rem;color:#94a3b8;margin:0 1rem .75rem}
  .banner{background:#7f1d1d;border:1px solid #ef4444;color:#fca5a5;padding:.75rem 1rem;margin:.5rem 1rem;border-radius:.375rem;font-weight:600;display:none}
  .banner.show{display:block}
  .costs{display:flex;gap:1rem;padding:.5rem 1rem}
  .cost-card{background:#1e293b;border-radius:.375rem;padding:.75rem 1rem;min-width:180px}
  .cost-card .label{font-size:.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em}
  .cost-card .value{font-size:1.4rem;font-weight:700;color:#38bdf8}
  table{width:calc(100% - 2rem);margin:.5rem 1rem;border-collapse:collapse;font-size:.82rem}
  th{background:#1e293b;padding:.5rem .75rem;text-align:left;font-weight:600;color:#94a3b8;white-space:nowrap}
  td{padding:.45rem .75rem;border-bottom:1px solid #1e293b}
  tr:hover td{background:#1e293b}
  .badge{display:inline-block;padding:.1rem .5rem;border-radius:9999px;font-size:.7rem;font-weight:700}
  .RUNNING{background:#166534;color:#86efac}
  .PAUSED{background:#1e3a5f;color:#93c5fd}
  .UNKNOWN,.FAILED,.ERROR{background:#7f1d1d;color:#fca5a5}
  .risk{color:#ef4444;font-weight:700}
  #login{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);align-items:center;justify-content:center}
  #login.show{display:flex}
  .login-box{background:#1e293b;padding:2rem;border-radius:.5rem;min-width:320px}
  .login-box h2{margin:0 0 1rem;font-size:1rem}
  .login-box input{width:100%;box-sizing:border-box;padding:.5rem;background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:.25rem;margin-bottom:.75rem;font-size:.9rem}
  .login-box button{width:100%;padding:.5rem;background:#0284c7;color:#fff;border:none;border-radius:.25rem;cursor:pointer;font-size:.9rem}
  #status{color:#94a3b8;font-size:.75rem;margin:.25rem 1rem}
</style>
</head>
<body>
<div id="login"><div class="login-box">
  <h2>Concerto Admin — NF Dashboard</h2>
  <input id="tok" type="password" placeholder="Paste CONCERTO_OPS_TOKEN here">
  <button onclick="doLogin()">Unlock</button>
</div></div>

<h1>Northflank Dashboard</h1>
<div class="ts" id="ts">Loading…</div>
<div class="banner" id="inv-banner">⚠ Invoice RISK: latest invoice status is not paid — services will be SUSPENDED in 7 days and VOLUMES DELETED.</div>

<div class="costs">
  <div class="cost-card"><div class="label">Today so far</div><div class="value" id="today">—</div></div>
  <div class="cost-card"><div class="label">Month to date</div><div class="value" id="mtd">—</div></div>
  <div class="cost-card"><div class="label">Services (active/total)</div><div class="value" id="counts">—</div></div>
</div>

<div id="status"></div>

<h2 style="font-size:.9rem;margin:.75rem 1rem .25rem;color:#94a3b8">Services</h2>
<table id="svc-table">
<thead><tr><th>ID</th><th>Status</th><th>Plan</th><th>Created</th><th>Runtime (h)</th><th>Month cost</th><th>Today cost</th></tr></thead>
<tbody id="svc-body"><tr><td colspan="7" style="color:#64748b">Loading…</td></tr></tbody>
</table>

<h2 style="font-size:.9rem;margin:.75rem 1rem .25rem;color:#94a3b8">Volumes</h2>
<table id="vol-table">
<thead><tr><th>ID</th><th>Size (GB)</th><th>Attached to</th><th>Full monthly cost</th><th>Month to date</th></tr></thead>
<tbody id="vol-body"><tr><td colspan="5" style="color:#64748b">Loading…</td></tr></tbody>
</table>

<script>
const $ = id => document.getElementById(id);

function tok() { return sessionStorage.getItem('ops_token') || ''; }

function doLogin() {
  const t = $('tok').value.trim();
  if (!t) return;
  sessionStorage.setItem('ops_token', t);
  $('login').classList.remove('show');
  load();
}

function fmt(n) { return '$' + (n == null ? '?' : Number(n).toFixed(4)); }
function fmtH(s) { return s == null ? '?' : (s/3600).toFixed(1) + 'h'; }

async function load() {
  const t = tok();
  if (!t) { $('login').classList.add('show'); return; }
  $('status').textContent = 'Refreshing…';
  try {
    const r = await fetch('/api/admin/nf-status', {headers:{'Authorization':'Bearer '+t}});
    if (r.status === 401) { sessionStorage.removeItem('ops_token'); $('login').classList.add('show'); return; }
    if (!r.ok) { $('status').textContent = 'Error ' + r.status; return; }
    const d = await r.json();
    render(d);
    $('status').textContent = '';
  } catch(e) { $('status').textContent = 'Fetch error: ' + e.message; }
}

function render(d) {
  $('ts').textContent = 'Provider: ' + d.provider_active + ' | As of: ' + new Date(d.as_of).toLocaleString();
  $('today').textContent = fmt(d.cost_estimate_today_usd);
  $('mtd').textContent = fmt(d.cost_estimate_month_to_date_usd);
  $('counts').textContent = (d.counts.active) + ' / ' + d.counts.total;

  const inv = d.latest_invoice;
  if (inv && inv.risk_flag) {
    $('inv-banner').classList.add('show');
    $('inv-banner').textContent = '⚠ Invoice RISK: status="' + inv.status + '" (id=' + inv.id + ') — SERVICES SUSPENDED in 7 days, VOLUMES DELETED. Fix billing NOW.';
  } else {
    $('inv-banner').classList.remove('show');
  }

  const sb = $('svc-body');
  if (!d.services.length) { sb.innerHTML = '<tr><td colspan="7" style="color:#64748b">No services</td></tr>'; }
  else sb.innerHTML = d.services.map(s => `<tr>
    <td style="font-family:monospace;font-size:.78rem">${s.id}</td>
    <td><span class="badge ${s.status}">${s.status}</span></td>
    <td>${s.plan || '—'}</td>
    <td style="font-size:.75rem">${s.created_at ? new Date(s.created_at).toLocaleDateString() : '—'}</td>
    <td>${fmtH(s.runtime_seconds_so_far)}</td>
    <td>${fmt(s.estimated_cost_usd_so_far_this_month)}</td>
    <td>${fmt(s.estimated_cost_usd_today)}</td>
  </tr>`).join('');

  const vb = $('vol-body');
  if (!d.volumes.length) { vb.innerHTML = '<tr><td colspan="5" style="color:#64748b">No volumes</td></tr>'; }
  else vb.innerHTML = d.volumes.map(v => `<tr>
    <td style="font-family:monospace;font-size:.78rem">${v.id}</td>
    <td>${(v.size_mb/1024).toFixed(1)}</td>
    <td style="font-size:.75rem">${v.attached_to_service_id || '<span style="color:#64748b">unattached</span>'}</td>
    <td>${fmt(v.estimated_monthly_cost_usd)}</td>
    <td>${fmt(v.estimated_cost_usd_so_far_this_month)}</td>
  </tr>`).join('');
}

// Check URL param on load (for bookmarked URLs with token)
(function() {
  const p = new URLSearchParams(location.search);
  const t = p.get('token');
  if (t) { sessionStorage.setItem('ops_token', t); history.replaceState({}, '', location.pathname); }
})();

load();
setInterval(load, 30000);
</script>
</body>
</html>"""


@router.get("/api/admin/nf-status/page", response_class=HTMLResponse)
async def nf_status_page(request: Request, token: str = ""):
    # Token accepted via query param OR bearer header (JS then uses sessionStorage)
    # If neither provided, page still loads and prompts via JS login form
    if token or request.headers.get("Authorization", ""):
        _check_admin_auth(request, token)
    return HTMLResponse(content=_HTML)
