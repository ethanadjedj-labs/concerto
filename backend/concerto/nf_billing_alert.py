"""Northflank billing-alert cron — prevents surprise invoices and service suspension.

Run hourly by concerto-nf-billing-alert.timer. Manual invocation:
    python -m concerto.nf_billing_alert

Dry-run (prints alerts, no emails sent):
    CONCERTO_NF_ALERT_DRY_RUN=1 python -m concerto.nf_billing_alert

Tunable thresholds (env vars with sane defaults):
    CONCERTO_NF_ALERT_MTD_USD            default 100   alert when MTD cost > $100
    CONCERTO_NF_ALERT_RATE_USD_PER_DAY   default 50    alert when daily burn > $50/day
    CONCERTO_NF_ALERT_MAX_SERVICES       default 200   alert when active services > 200
    CONCERTO_NF_ALERT_INVOICE_AGE_DAYS   default 2     alert when open invoice > 2 days old

NF BILLING RISK MODEL:
    NF auto-charges when usage hits a threshold.  If the card charge fails:
      Day 7:  Services SUSPENDED (all customer workspaces offline)
      Day 14: Volumes PERMANENTLY DELETED (customer data lost forever)
    This script catches the warning signs well before either deadline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone

import httpx

from concerto.email_utils import send_operator_alert

logger = logging.getLogger(__name__)

# ── Northflank API ─────────────────────────────────────────────────────────────
_NF_API_BASE = "https://api.northflank.com"
_NF_API_TOKEN = os.getenv("CONCERTO_NF_API_TOKEN", "")
_NF_PROJECT_ID = os.getenv("CONCERTO_NF_PROJECT_ID", "concerto")

# ── Pricing constants — verified against GET /v1/plans 2026-05-20 ─────────────
# Source: result-billing.md + provider_northflank.py
_PLAN_HOURLY_USD: dict[str, float] = {
    "nf-compute-20":    0.008,  # shared, 0.2 vCPU / 0.5 GB
    "nf-compute-100-1": 0.025,  # 1 vCPU / 2 GB
    "nf-compute-200":   0.067,  # 2 vCPU / 4 GB (SOLO plan) — verified 2026-05-20
    "nf-compute-200-8": 0.072,  # 2 vCPU / 8 GB (PRO plan)  — verified 2026-05-20
}
_VOLUME_USD_PER_GB_MONTH: float = 0.15  # NVMe SSD — verified 2026-05-20
_VOLUME_BILLING_DAYS: int = 30          # NF prorates storage over a 30-day billing period

# ── Alert thresholds — tune via env vars ───────────────────────────────────────
_ALERT_MTD_USD      = float(os.getenv("CONCERTO_NF_ALERT_MTD_USD",          "100"))
_ALERT_RATE_PER_DAY = float(os.getenv("CONCERTO_NF_ALERT_RATE_USD_PER_DAY", "50"))
_ALERT_MAX_SERVICES = int(os.getenv("CONCERTO_NF_ALERT_MAX_SERVICES",        "200"))
_ALERT_INVOICE_DAYS = float(os.getenv("CONCERTO_NF_ALERT_INVOICE_AGE_DAYS", "2"))

# ── Runtime options ────────────────────────────────────────────────────────────
_STATE_PATH = os.getenv(
    "CONCERTO_NF_ALERT_STATE_PATH", "/var/lib/concerto/nf_alert_state.json"
)
_DRY_RUN = os.getenv("CONCERTO_NF_ALERT_DRY_RUN", "0") == "1"


# ── Timestamp parsing ──────────────────────────────────────────────────────────

def _parse_ts(ts_str):
    """Parse ISO 8601 string or numeric timestamp to float. Returns 0.0 on failure."""
    if ts_str is None or ts_str == "":
        return 0.0
    try:
        if isinstance(ts_str, (int, float)):
            return float(ts_str)
        s = str(ts_str).rstrip("Z")
        if "T" in s:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        return float(ts_str)
    except Exception:
        return 0.0


# ── Cost computation ───────────────────────────────────────────────────────────

def compute_costs(services, volumes, now_ts=None):
    """
    Compute month-to-date estimated cost from NF API service and volume lists.

    Pure function — no API calls. Takes synthetic or real NF API records.

    Returns a dict with:
        mtd_compute_usd, mtd_volume_usd, mtd_total_usd,
        daily_rate_usd, active_service_count, service_breakdown,
        hours_elapsed_this_month, days_elapsed
    """
    if now_ts is None:
        now_ts = time.time()

    now_utc = datetime.fromtimestamp(now_ts, tz=timezone.utc)
    month_start = datetime(now_utc.year, now_utc.month, 1, tzinfo=timezone.utc)
    month_start_ts = month_start.timestamp()

    hours_elapsed = (now_ts - month_start_ts) / 3600
    days_elapsed = hours_elapsed / 24

    compute_usd = 0.0
    service_breakdown = []

    for svc in services:
        plan = svc.get("billing", {}).get("deploymentPlan", "")
        hourly = _PLAN_HOURLY_USD.get(plan, 0.0)

        created_ts = _parse_ts(svc.get("createdAt"))
        # If created this month, bill from creation; otherwise bill from month start
        bill_start_ts = max(month_start_ts, created_ts) if created_ts else month_start_ts
        hours_billed = max(0.0, (now_ts - bill_start_ts) / 3600)

        svc_cost = hourly * hours_billed
        compute_usd += svc_cost
        service_breakdown.append({
            "name": svc.get("name", "?"),
            "plan": plan,
            "hourly_usd": hourly,
            "hours_billed": round(hours_billed, 1),
            "cost_usd": round(svc_cost, 4),
        })

    volume_usd = 0.0
    # Hourly rate: $0.15 / GB-month / (30 days/month * 24 h/day)
    _hourly_per_gb = _VOLUME_USD_PER_GB_MONTH / (_VOLUME_BILLING_DAYS * 24)
    for vol in volumes:
        size_mb = vol.get("spec", {}).get("storageSize", 0)
        size_gb = size_mb / 1024

        created_ts = _parse_ts(vol.get("createdAt"))
        bill_start_ts = max(month_start_ts, created_ts) if created_ts else month_start_ts
        hours_billed = max(0.0, (now_ts - bill_start_ts) / 3600)

        volume_usd += size_gb * _hourly_per_gb * hours_billed

    mtd_total = compute_usd + volume_usd
    daily_rate = mtd_total / days_elapsed if days_elapsed > 0 else 0.0

    return {
        "mtd_compute_usd": round(compute_usd, 4),
        "mtd_volume_usd": round(volume_usd, 4),
        "mtd_total_usd": round(mtd_total, 4),
        "daily_rate_usd": round(daily_rate, 4),
        "active_service_count": len(services),
        "hours_elapsed_this_month": round(hours_elapsed, 2),
        "days_elapsed": round(days_elapsed, 4),
        "service_breakdown": service_breakdown,
    }


# ── Alert-state helpers ────────────────────────────────────────────────────────

def _load_state():
    try:
        with open(_STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(state):
    try:
        os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
        with open(_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as exc:
        logger.warning("Failed to save alert state to %s: %s", _STATE_PATH, exc)


def _should_alert(state, key, current_value, threshold):
    """
    Return True if an alert should fire for this condition.

    Fires when condition is active (current_value > threshold) AND one of:
      - Never alerted before for this key
      - Value has worsened by 25% or more since last alert
    Clears automatically when condition becomes inactive.
    """
    if current_value <= threshold:
        return False

    prior = state.get(key)
    if prior is None:
        return True

    last_value = prior.get("value", 0.0)
    return current_value >= last_value * 1.25


# ── Alert formatting ───────────────────────────────────────────────────────────

def _fmt_cost_body(costs, headline):
    lines = [
        headline,
        "",
        "Month-to-date compute:   $%.2f" % costs["mtd_compute_usd"],
        "Month-to-date storage:   $%.2f" % costs["mtd_volume_usd"],
        "Month-to-date TOTAL:     $%.2f" % costs["mtd_total_usd"],
        "Days elapsed this month: %.1f" % costs["days_elapsed"],
        "Extrapolated daily rate: $%.2f/day" % costs["daily_rate_usd"],
        "Active services:         %d" % costs["active_service_count"],
        "",
        "Service breakdown:",
    ]
    for s in costs.get("service_breakdown", []):
        lines.append(
            "  %-30s  %-20s  $%.3f/hr x %.0fh = $%.2f"
            % (s["name"], s["plan"], s["hourly_usd"], s["hours_billed"], s["cost_usd"])
        )
    lines += [
        "",
        "--- NORTHFLANK BILLING RISK -------------------------------------------",
        "NF auto-invoices when usage crosses a threshold. If the charge fails:",
        "  Day 7:  Services SUSPENDED -- all customer workspaces go offline",
        "  Day 14: Volumes PERMANENTLY DELETED -- customer data lost",
        "",
        "Review usage: https://app.northflank.com",
        "Billing page: https://app.northflank.com/billing",
    ]
    return "\n".join(lines)


def _latest_invoice(invoices):
    if not invoices:
        return None
    return max(invoices, key=lambda inv: _parse_ts(inv.get("createdAt", "")))


def _check_invoice_alert(state, invoice, now_ts):
    """Return (subject, body) if invoice warrants an alert, else None."""
    status = (invoice.get("status") or "").lower()
    if status != "open":
        state.pop("invoice", None)
        return None

    invoice_id = invoice.get("id", "unknown")
    created_ts = _parse_ts(invoice.get("createdAt"))
    age_hours = (now_ts - created_ts) / 3600 if created_ts else 0.0

    if age_hours < _ALERT_INVOICE_DAYS * 24:
        return None  # too new to be a payment-failure concern

    prior = state.get("invoice", {})
    prior_id = prior.get("id", "")
    prior_ts = prior.get("ts", 0.0)

    # Re-alert for: new invoice, first alert ever, or 12+ hours since last alert
    if prior_id == invoice_id and prior_ts > 0 and (now_ts - prior_ts) < 12 * 3600:
        return None

    days_open = age_hours / 24
    days_until_suspension = max(0.0, 7.0 - days_open)
    days_until_deletion = max(0.0, 14.0 - days_open)

    subject = (
        "[NF-BILLING] URGENT: Invoice open %.1fd"
        " -- suspension in %.1fd, volume deletion in %.1fd"
        % (days_open, days_until_suspension, days_until_deletion)
    )
    body = "\n".join([
        "URGENT: Northflank invoice %s has status OPEN for %.1f days." % (invoice_id, days_open),
        "",
        "  Suspension deadline:       %.1f days from now" % days_until_suspension,
        "  VOLUME DELETION deadline:  %.1f days from now" % days_until_deletion,
        "",
        "NF BEHAVIOR ON FAILED PAYMENT:",
        "  Day 0:  Invoice auto-generated and charge attempted",
        "  Day 7:  Services SUSPENDED (customer workspaces go offline)",
        "  Day 14: Volumes PERMANENTLY DELETED (customer data lost forever)",
        "",
        "ACTION REQUIRED:",
        "  1. Log in to Northflank: https://app.northflank.com",
        "  2. Go to Billing -> Invoices",
        "  3. Update payment method or pay invoice manually",
        "  4. Confirm all services resume after payment clears",
        "",
        "Invoice ID:     %s" % invoice_id,
        "Invoice status: %s" % invoice.get("status", "unknown"),
        "Invoice amount: %s" % invoice.get("amount", invoice.get("total", "unknown")),
    ])
    return subject, body


# ── Alert dispatch ─────────────────────────────────────────────────────────────

async def _send_alert(subject, body):
    if _DRY_RUN:
        print("\n" + "=" * 64)
        print("DRY-RUN -- would send operator alert:")
        print("Subject: " + subject)
        print("Body:\n" + body)
        print("=" * 64)
    else:
        await send_operator_alert(subject, body)
        logger.warning("[NF-BILLING] Alert sent: %s", subject)


# ── NF API calls ───────────────────────────────────────────────────────────────

def _nf_headers():
    return {
        "Authorization": "Bearer " + _NF_API_TOKEN,
        "Content-Type": "application/json",
    }


def _extract_records(data):
    """Extract records list from NF API response, tolerating different shapes."""
    inner = data.get("data", data)
    if isinstance(inner, list):
        return inner
    if isinstance(inner, dict):
        records = inner.get("records", inner.get("items", []))
        if isinstance(records, list):
            return records
    return []


async def _fetch_services(client):
    resp = await client.get("/v1/projects/%s/services" % _NF_PROJECT_ID)
    resp.raise_for_status()
    return _extract_records(resp.json())


async def _fetch_volumes(client):
    resp = await client.get("/v1/projects/%s/volumes" % _NF_PROJECT_ID)
    resp.raise_for_status()
    return _extract_records(resp.json())


async def _fetch_invoices(client):
    resp = await client.get("/v1/billing/invoices")
    resp.raise_for_status()
    return _extract_records(resp.json())


# ── Main check ─────────────────────────────────────────────────────────────────

async def run_billing_check():
    """Fetch NF state, compute costs, and fire alerts as needed. Returns summary."""
    if not _NF_API_TOKEN:
        logger.error("[NF-BILLING] CONCERTO_NF_API_TOKEN not set -- cannot check billing")
        print("[NF-BILLING] ERROR: CONCERTO_NF_API_TOKEN not configured")
        return {"error": "no_token"}

    try:
        async with httpx.AsyncClient(
            base_url=_NF_API_BASE, headers=_nf_headers(), timeout=30
        ) as client:
            results = await asyncio.gather(
                _fetch_services(client),
                _fetch_volumes(client),
                _fetch_invoices(client),
                return_exceptions=True,
            )
    except Exception as exc:
        logger.error("[NF-BILLING] HTTP client error: %s", exc)
        return {"error": str(exc)}

    services, volumes, invoices = results

    if isinstance(services, Exception):
        logger.warning("[NF-BILLING] services fetch failed: %s", services)
        services = []
    if isinstance(volumes, Exception):
        logger.warning("[NF-BILLING] volumes fetch failed: %s", volumes)
        volumes = []
    if isinstance(invoices, Exception):
        logger.warning("[NF-BILLING] invoices fetch failed: %s", invoices)
        invoices = []

    costs = compute_costs(services, volumes)
    state = _load_state()
    now_ts = time.time()
    alerts_fired = []

    # ── Alert 1: Month-to-date cost ────────────────────────────────────────────
    mtd = costs["mtd_total_usd"]
    if _should_alert(state, "mtd", mtd, _ALERT_MTD_USD):
        subject = "[NF-BILLING] MTD cost $%.2f exceeds $%.0f threshold" % (mtd, _ALERT_MTD_USD)
        body = _fmt_cost_body(
            costs,
            "Month-to-date NF cost $%.2f has exceeded the $%.0f alert threshold." % (mtd, _ALERT_MTD_USD),
        )
        await _send_alert(subject, body)
        state["mtd"] = {"value": mtd, "ts": now_ts}
        alerts_fired.append("mtd")
    elif mtd <= _ALERT_MTD_USD:
        state.pop("mtd", None)

    # ── Alert 2: Daily burn rate ───────────────────────────────────────────────
    rate = costs["daily_rate_usd"]
    if _should_alert(state, "rate", rate, _ALERT_RATE_PER_DAY):
        subject = "[NF-BILLING] Daily burn $%.2f/day exceeds $%.0f/day threshold" % (rate, _ALERT_RATE_PER_DAY)
        body = _fmt_cost_body(
            costs,
            "Extrapolated daily burn $%.2f/day exceeds the $%.0f/day threshold.\n"
            "This is an early-warning indicator of runaway compute costs." % (rate, _ALERT_RATE_PER_DAY),
        )
        await _send_alert(subject, body)
        state["rate"] = {"value": rate, "ts": now_ts}
        alerts_fired.append("rate")
    elif rate <= _ALERT_RATE_PER_DAY:
        state.pop("rate", None)

    # ── Alert 3: Open invoice (payment failure countdown) ──────────────────────
    latest_inv = _latest_invoice(invoices)
    if latest_inv:
        invoice_alert = _check_invoice_alert(state, latest_inv, now_ts)
        if invoice_alert:
            subject, body = invoice_alert
            await _send_alert(subject, body)
            state["invoice"] = {
                "id": latest_inv.get("id", ""),
                "ts": now_ts,
            }
            alerts_fired.append("invoice")
    else:
        state.pop("invoice", None)

    # ── Alert 4: Active service count (orphan / runaway detection) ─────────────
    svc_count = costs["active_service_count"]
    if _should_alert(state, "service_count", float(svc_count), float(_ALERT_MAX_SERVICES)):
        subject = (
            "[NF-BILLING] Active service count %d exceeds %d -- possible runaway provisioning"
            % (svc_count, _ALERT_MAX_SERVICES)
        )
        body = "\n".join([
            "ACTIVE SERVICE COUNT: %d (threshold: %d)" % (svc_count, _ALERT_MAX_SERVICES),
            "",
            "This may indicate an orphan-accumulation bug or runaway provisioning loop.",
            "Each extra service costs $0.067/hr or more in compute.",
            "",
            "MTD compute estimate: $%.2f" % costs["mtd_compute_usd"],
            "MTD storage estimate: $%.2f" % costs["mtd_volume_usd"],
            "MTD total:            $%.2f" % costs["mtd_total_usd"],
            "",
            "Inspect services: https://app.northflank.com",
        ])
        await _send_alert(subject, body)
        state["service_count"] = {"value": float(svc_count), "ts": now_ts}
        alerts_fired.append("service_count")
    elif svc_count <= _ALERT_MAX_SERVICES:
        state.pop("service_count", None)

    _save_state(state)

    mode = "DRY-RUN " if _DRY_RUN else ""
    print(
        "[NF-BILLING] %scheck complete: mtd=$%.2f rate=$%.2f/day services=%d volumes=%d alerts=%s"
        % (mode, mtd, rate, svc_count, len(volumes) if isinstance(volumes, list) else 0, alerts_fired)
    )

    return {
        "mtd_total_usd": mtd,
        "daily_rate_usd": rate,
        "active_services": svc_count,
        "active_volumes": len(volumes) if isinstance(volumes, list) else 0,
        "alerts_fired": alerts_fired,
        "dry_run": _DRY_RUN,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    async def _main():
        result = await run_billing_check()
        if result.get("error"):
            raise SystemExit(1)

    asyncio.run(_main())
