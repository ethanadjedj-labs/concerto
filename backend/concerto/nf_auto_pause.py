"""Auto-pause idle Northflank environments — run every 5 min via systemd timer.

Economic justification:
  NF compute billing stops immediately on pause (POST .../pause → instances=0).
  Volume ($0.90/mo for 6 GB) is charged whether paused or not.
  Resume latency: ~11-15 s (PROVEN, result-billing.md).

Pause eligibility:
  - provider = 'northflank'
  - status in PAUSEABLE_STATUSES (never 'installing', 'awaiting_oauth', etc.)
  - runtime_state is NOT already 'paused'
  - vps_id is set
  - last_active_at IS NOT NULL and older than PAUSE_AFTER_S seconds

Threshold trade-offs:
  PAUSE_AFTER_S=1800 (30 min): balances cost vs. resume UX (11 s wake).
  Smaller (e.g. 300 s) → higher savings, more frequent "Waking…" interruptions.
  Larger (e.g. 3600 s) → smoother UX, higher idle cost.
  Set CONCERTO_PAUSE_AFTER_S in environment to override.

DRY_RUN mode:
  Set CONCERTO_PAUSE_DRY_RUN=1 to log what would be paused without acting.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import sys
import time

from concerto import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s nf_auto_pause %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_DB_PATH = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
_PAUSE_AFTER_S = int(os.getenv("CONCERTO_PAUSE_AFTER_S", "1800"))
_DRY_RUN = os.getenv("CONCERTO_PAUSE_DRY_RUN", "0").strip() not in ("", "0", "false", "no")

# Statuses that represent a fully-provisioned, running workspace.
# We NEVER pause: installing, provisioning*, awaiting_oauth, *_failed, refunded, etc.
PAUSEABLE_STATUSES = frozenset({
    "active",
    "oauth_complete",
    "mcp_active",
    "connector_first_call_detected",
})


def _get_eligible_buyers(now: int) -> list[dict]:
    """Return buyers eligible for auto-pause."""
    threshold = now - _PAUSE_AFTER_S
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT token, vps_id, status, email, last_active_at, runtime_state
                FROM concerto_buyers
                WHERE provider = 'northflank'
                  AND status IN ({placeholders})
                  AND (runtime_state IS NULL OR runtime_state != 'paused')
                  AND vps_id IS NOT NULL AND vps_id != ''
                  AND last_active_at IS NOT NULL
                  AND last_active_at < ?
                """.format(
                    placeholders=",".join("?" * len(PAUSEABLE_STATUSES))
                ),
                (*PAUSEABLE_STATUSES, threshold),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as exc:
        logger.error("DB query failed: %s", exc)
        return []


def _set_runtime_paused(token: str, now: int) -> None:
    """Mark buyer as runtime-paused in DB."""
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=10)
        try:
            conn.execute(
                "UPDATE concerto_buyers SET runtime_state = 'paused' WHERE token = ?",
                (token,),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.error("DB update failed for token %.8s: %s", token, exc)


async def run_pause_pass() -> dict:
    """Main reconciliation pass.  Returns summary dict."""
    from concerto import provider_factory as provisioner  # lazy import (needs env)

    now = int(time.time())
    buyers = _get_eligible_buyers(now)

    paused = 0
    skipped = 0
    errors: list[str] = []

    for buyer in buyers:
        token = buyer["token"]
        vps_id = buyer["vps_id"]
        email = buyer.get("email", "")[:40]
        last_active = buyer.get("last_active_at", 0)
        idle_s = now - last_active

        if _DRY_RUN:
            logger.info(
                "DRY_RUN would pause token=%.8s email=%s vps_id=%s idle=%ds",
                token, email, vps_id, idle_s,
            )
            paused += 1
            continue

        logger.info(
            "Pausing idle workspace token=%.8s email=%s vps_id=%s idle=%ds (threshold=%ds)",
            token, email, vps_id, idle_s, _PAUSE_AFTER_S,
        )
        try:
            await provisioner.suspend(api_key="", vps_id=vps_id)
            _set_runtime_paused(token, now)
            await db.log_lifecycle_event("pause", token, vps_id=vps_id, idle_seconds=idle_s, source="auto_pause")
            paused += 1
            logger.info("Paused OK: token=%.8s vps_id=%s", token, vps_id)
        except Exception as exc:
            err = f"pause_failed:{token[:8]}:{exc}"
            errors.append(err)
            logger.error("Pause failed token=%.8s vps_id=%s: %s", token, vps_id, exc)

    summary = {
        "dry_run": _DRY_RUN,
        "eligible": len(buyers),
        "paused": paused,
        "skipped": skipped,
        "errors": errors,
        "pause_after_s": _PAUSE_AFTER_S,
    }
    logger.info("Pass complete: %s", summary)
    return summary


if __name__ == "__main__":
    result = asyncio.run(run_pause_pass())
    print(json.dumps(result))
    if result["errors"]:
        sys.exit(1)
