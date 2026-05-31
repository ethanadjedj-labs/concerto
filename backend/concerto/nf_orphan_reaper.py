"""Northflank orphan reaper — reconciles actual NF resources against concerto_buyers.

Runs every 30 minutes via concerto-nf-orphan-reaper.timer.

Lists real NF services + volumes, cross-references against concerto_buyers by the
deterministic naming convention:
  service: concerto-{token[:8]}
  volume:  cvol-{token[:8]}

Any NF resource with no corresponding LIVE buyer row is an orphan.

DRY_RUN mode (default OFF — set CONCERTO_NF_ORPHAN_DRY_RUN=1 to log-only):
  Logs orphans but does not destroy them.

Safety guards (always active, even in live mode):
  - Never destroys a resource whose token maps to a buyer row in a LIVE status.
  - Unknown/unexpected buyer status → FLAG, not destroy.
  - Double-checks DB immediately before each destruction call.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sqlite3
import sys

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s nf_orphan_reaper %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_NF_API_BASE = "https://api.northflank.com"
_NF_API_TOKEN = os.getenv("CONCERTO_NF_API_TOKEN", "")
_NF_PROJECT_ID = os.getenv("CONCERTO_NF_PROJECT_ID", "concerto")
_DB_PATH = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
_DRY_RUN = os.getenv("CONCERTO_NF_ORPHAN_DRY_RUN", "0").strip() not in ("", "0", "false", "no")

# Buyer statuses that represent an actively-used resource — never destroy.
LIVE_STATUSES = frozenset({
    "paid_unprovisioned",
    "provisioning",
    "installing",
    "awaiting_oauth",
    "active",
    "oauth_complete",
    "mcp_active",
    "connector_first_call_detected",
    "provision_failed",
    "suspended",
    "payment_failed",
})

# Buyer statuses that are fully terminal — resource cleanup is permitted.
TERMINAL_STATUSES = frozenset({
    "trial_expired",
    "refunded",
    "trial_upgraded",
    "destroyed",
    "expired",
})


def _nf_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_NF_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _extract_records(data: dict) -> list[dict]:
    inner = data.get("data", data)
    if isinstance(inner, list):
        return inner
    if isinstance(inner, dict):
        records = inner.get("records", inner.get("items", []))
        if isinstance(records, list):
            return records
    return []


async def _fetch_all_services(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(f"/v1/projects/{_NF_PROJECT_ID}/services")
    resp.raise_for_status()
    return _extract_records(resp.json())


async def _fetch_all_volumes(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(f"/v1/projects/{_NF_PROJECT_ID}/volumes")
    resp.raise_for_status()
    return _extract_records(resp.json())


def _get_buyer_by_vps_id(vps_id: str, db_path: str = "") -> dict | None:
    path = db_path or _DB_PATH
    try:
        conn = sqlite3.connect(path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT token, status, email FROM concerto_buyers"
                " WHERE vps_id = ? AND provider = 'northflank'",
                (vps_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    except Exception as exc:
        logger.error("DB query failed (vps_id=%s): %s", vps_id, exc)
        return None


def _get_db_nf_active_count(db_path: str = "") -> int:
    path = db_path or _DB_PATH
    live_ph = ",".join("?" * len(LIVE_STATUSES))
    try:
        conn = sqlite3.connect(path, timeout=10)
        try:
            row = conn.execute(
                f"SELECT COUNT(*) FROM concerto_buyers"
                f" WHERE provider='northflank' AND status IN ({live_ph})",
                tuple(LIVE_STATUSES),
            ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()
    except Exception as exc:
        logger.error("DB count query failed: %s", exc)
        return 0


def _is_concerto_service(name: str) -> bool:
    """Match NF service names managed by this provisioner: concerto-XXXXXXXX."""
    if not name.startswith("concerto-"):
        return False
    suffix = name[len("concerto-"):]
    return bool(suffix) and bool(re.match(r"^[a-z0-9-]{1,8}$", suffix))


def _is_concerto_volume(name: str) -> bool:
    """Match NF volume names managed by this provisioner: cvol-XXXXXXXX."""
    if not name.startswith("cvol-"):
        return False
    suffix = name[len("cvol-"):]
    return bool(suffix) and bool(re.match(r"^[a-z0-9-]{1,8}$", suffix))


async def _destroy_service(client: httpx.AsyncClient, service_name: str) -> None:
    resp = await client.delete(f"/v1/projects/{_NF_PROJECT_ID}/services/{service_name}")
    if resp.status_code not in (200, 204, 404):
        raise RuntimeError(
            f"DELETE service {service_name} returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    logger.warning("ORPHAN-REAPER DESTROYED service: %s", service_name)


async def _destroy_volume(client: httpx.AsyncClient, volume_name: str) -> None:
    resp = await client.delete(f"/v1/projects/{_NF_PROJECT_ID}/volumes/{volume_name}")
    if resp.status_code not in (200, 204, 404):
        raise RuntimeError(
            f"DELETE volume {volume_name} returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    logger.warning("ORPHAN-REAPER DESTROYED volume: %s", volume_name)


def _classify_resource(
    resource_label: str,
    service_name: str,
    db_path: str = "",
) -> tuple[str, dict | None]:
    """
    Return (classification, buyer_row).

    classification:
      'live'      — has a live buyer, leave alone
      'orphan'    — no buyer row OR terminal buyer, safe to destroy
      'protected' — buyer with unknown status, flag only
    """
    buyer = _get_buyer_by_vps_id(service_name, db_path)

    if buyer is None:
        logger.warning("ORPHAN: %s has NO buyer row in DB", resource_label)
        return "orphan", None

    if buyer["status"] in LIVE_STATUSES:
        return "live", buyer

    if buyer["status"] in TERMINAL_STATUSES:
        logger.warning(
            "ORPHAN: %s has terminal buyer (status=%s email=%s) — resource leaked",
            resource_label, buyer["status"], (buyer.get("email") or "")[:40],
        )
        return "orphan", buyer

    logger.warning(
        "ORPHAN-FLAG: %s buyer status=%s unknown — flagging, not destroying",
        resource_label, buyer["status"],
    )
    return "protected", buyer


async def run_orphan_pass(db_path: str = "", dry_run: bool | None = None) -> dict:
    """Main reconciliation pass. Returns summary dict."""
    _db = db_path or _DB_PATH
    _dr = _DRY_RUN if dry_run is None else dry_run

    if not _NF_API_TOKEN:
        logger.error("ORPHAN-REAPER: CONCERTO_NF_API_TOKEN not set — cannot reconcile")
        return {"error": "no_token"}

    try:
        async with httpx.AsyncClient(
            base_url=_NF_API_BASE, headers=_nf_headers(), timeout=30
        ) as client:
            services_result, volumes_result = await asyncio.gather(
                _fetch_all_services(client),
                _fetch_all_volumes(client),
                return_exceptions=True,
            )
    except Exception as exc:
        logger.error("ORPHAN-REAPER: HTTP client error: %s", exc)
        return {"error": str(exc)}

    if isinstance(services_result, Exception):
        logger.error("ORPHAN-REAPER: Failed to list NF services: %s", services_result)
        return {"error": f"services_fetch_failed: {services_result}"}

    if isinstance(volumes_result, Exception):
        logger.error("ORPHAN-REAPER: Failed to list NF volumes: %s", volumes_result)
        return {"error": f"volumes_fetch_failed: {volumes_result}"}

    services: list[dict] = services_result
    volumes: list[dict] = volumes_result

    # ── Divergence alarm ───────────────────────────────────────────────────────
    db_active = _get_db_nf_active_count(_db)
    nf_svc_count = len(services)
    if nf_svc_count != db_active:
        logger.warning(
            "ORPHAN-REAPER DIVERGENCE: NF has %d service(s) but DB tracks %d active NF buyer(s)",
            nf_svc_count, db_active,
        )

    orphaned_services: list[str] = []
    orphaned_volumes: list[str] = []
    protected: list[str] = []
    destroyed_services: list[str] = []
    destroyed_volumes: list[str] = []
    errors: list[str] = []

    # ── Service reconciliation ─────────────────────────────────────────────────
    for svc in services:
        name = svc.get("name", "")
        if not _is_concerto_service(name):
            continue
        classification, _ = _classify_resource(f"NF service {name}", name, _db)
        if classification == "orphan":
            orphaned_services.append(name)
        elif classification == "protected":
            protected.append(name)

    # ── Volume reconciliation ──────────────────────────────────────────────────
    for vol in volumes:
        name = vol.get("name", "")
        if not _is_concerto_volume(name):
            continue
        token_prefix = name[len("cvol-"):]
        corresponding_service = f"concerto-{token_prefix}"
        classification, _ = _classify_resource(
            f"NF volume {name}", corresponding_service, _db
        )
        if classification == "orphan":
            orphaned_volumes.append(name)
        elif classification == "protected":
            protected.append(name)

    # ── Destroy / dry-run report ───────────────────────────────────────────────
    if _dr:
        if orphaned_services or orphaned_volumes:
            logger.warning(
                "DRY_RUN: Would destroy %d service(s) %s and %d volume(s) %s",
                len(orphaned_services), orphaned_services,
                len(orphaned_volumes), orphaned_volumes,
            )
        else:
            logger.info("DRY_RUN: No orphans found — NF state matches DB (services=%d)", nf_svc_count)
    else:
        async with httpx.AsyncClient(
            base_url=_NF_API_BASE, headers=_nf_headers(), timeout=30
        ) as client:
            for svc_name in orphaned_services:
                # Safety double-check: re-query immediately before destruction
                buyer = _get_buyer_by_vps_id(svc_name, _db)
                if buyer and buyer["status"] in LIVE_STATUSES:
                    logger.warning(
                        "SAFETY ABORT: service %s buyer became LIVE between scan and destroy — skipping",
                        svc_name,
                    )
                    protected.append(svc_name)
                    continue
                try:
                    await _destroy_service(client, svc_name)
                    destroyed_services.append(svc_name)
                except Exception as exc:
                    err = f"destroy_service:{svc_name}:{exc}"
                    errors.append(err)
                    logger.error("Failed to destroy orphaned service %s: %s", svc_name, exc)

            for vol_name in orphaned_volumes:
                token_prefix = vol_name[len("cvol-"):]
                buyer = _get_buyer_by_vps_id(f"concerto-{token_prefix}", _db)
                if buyer and buyer["status"] in LIVE_STATUSES:
                    logger.warning(
                        "SAFETY ABORT: volume %s buyer became LIVE between scan and destroy — skipping",
                        vol_name,
                    )
                    protected.append(vol_name)
                    continue
                try:
                    await _destroy_volume(client, vol_name)
                    destroyed_volumes.append(vol_name)
                except Exception as exc:
                    err = f"destroy_volume:{vol_name}:{exc}"
                    errors.append(err)
                    logger.error("Failed to destroy orphaned volume %s: %s", vol_name, exc)

    summary = {
        "dry_run": _dr,
        "nf_services_total": nf_svc_count,
        "nf_volumes_total": len(volumes),
        "db_active_nf_count": db_active,
        "orphaned_services": orphaned_services,
        "orphaned_volumes": orphaned_volumes,
        "protected": protected,
        "destroyed_services": destroyed_services,
        "destroyed_volumes": destroyed_volumes,
        "errors": errors,
    }
    logger.info("Orphan reaper pass complete: %s", summary)
    return summary


if __name__ == "__main__":
    import asyncio as _asyncio

    result = _asyncio.run(run_orphan_pass())
    print(json.dumps(result, indent=2))
    if result.get("error") or result.get("errors"):
        sys.exit(1)
