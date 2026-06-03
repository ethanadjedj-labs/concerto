"""
Product-funnel metrics endpoint
================================

GET /api/admin/product-metrics  →  JSON snapshot of real funnel counts.

Everything in this response is computed from the production SQLite at
CONCERTO_DB_PATH (default `/var/lib/concerto/concerto.db`).  There are no
in-memory counters and no derived ratios — when the underlying tables are
empty, the numbers are zero, not invented.

Authentication mirrors `nf_admin_router.py`: bearer-only
(`Authorization: Bearer <CONCERTO_OPS_TOKEN>`) with constant-time
compare.  No query-string token is accepted (F-07 hardening).
"""

from __future__ import annotations

import hmac
import os
import sqlite3
import time

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

_OPS_TOKEN = os.getenv("CONCERTO_OPS_TOKEN", "")
_DB_PATH = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")


def _check_admin_auth(request: Request) -> None:
    if not _OPS_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="CONCERTO_OPS_TOKEN not configured",
        )
    auth = request.headers.get("Authorization", "")
    candidate = auth[7:] if auth.startswith("Bearer ") else ""
    if not candidate or not hmac.compare_digest(candidate, _OPS_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized — supply CONCERTO_OPS_TOKEN as Bearer token",
        )


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _count(conn: sqlite3.Connection, sql: str, *params) -> int:
    try:
        row = conn.execute(sql, params).fetchone()
    except sqlite3.OperationalError as exc:
        # Tables created outside the migration set (e.g. concerto_oauth_failures
        # which is provisioned by the installer, not a migration) may be
        # absent in fresh test DBs.  Treat that as zero rather than 500.
        if "no such table" in str(exc).lower():
            return 0
        raise
    if row is None:
        return 0
    return int(row[0] or 0)


_SUCCESS_STATES = (
    "awaiting_oauth", "active", "trial_expired", "trial_upgraded",
)
_FAILURE_STATES = (
    "provisioning_failed", "failed_install", "api_key_invalid",
    "account_no_credit", "provisioning_timeout",
)


@router.get("/api/admin/product-metrics")
async def product_metrics(request: Request) -> dict:
    _check_admin_auth(request)

    now_ts = int(time.time())
    day_ago = now_ts - 86_400
    week_ago = now_ts - 7 * 86_400

    conn = _conn()
    try:
        # Trials = rows created via /api/trial/start (plan='trial').
        trials_total = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE plan='trial'")
        trials_last_7d = _count(
            conn,
            "SELECT COUNT(*) FROM concerto_buyers WHERE plan='trial' AND paid_at >= ?",
            week_ago,
        )

        # Paid buyers = any non-trial plan (solo / pro / byoc / hosted).
        paid_total = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE plan != 'trial'")
        paid_last_7d = _count(
            conn,
            "SELECT COUNT(*) FROM concerto_buyers WHERE plan != 'trial' AND paid_at >= ?",
            week_ago,
        )

        # Funnel stages (across all plans).
        any_paid = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE paid_at IS NOT NULL")
        any_provisioned = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE provisioned_at IS NOT NULL")
        any_installed = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE installed_at IS NOT NULL")
        any_first_call = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE first_call_at IS NOT NULL")

        # Failure breakdown.
        placeholders = ",".join("?" * len(_FAILURE_STATES))
        failures_by_state: dict[str, int] = {}
        for row in conn.execute(
            f"SELECT status, COUNT(*) AS n FROM concerto_buyers "
            f"WHERE status IN ({placeholders}) GROUP BY status",
            _FAILURE_STATES,
        ):
            failures_by_state[row["status"]] = int(row["n"])

        refunded_total = _count(conn, "SELECT COUNT(*) FROM concerto_buyers WHERE refunded_at IS NOT NULL")

        # Lifecycle / engagement signal.
        lifecycle_events_total = _count(conn, "SELECT COUNT(*) FROM concerto_lifecycle_events")
        lifecycle_events_last_24h = _count(
            conn,
            "SELECT COUNT(*) FROM concerto_lifecycle_events WHERE ts >= ?",
            day_ago,
        )

        # Reliability signals from sibling tables.
        oauth_failures_total = _count(conn, "SELECT COUNT(*) FROM concerto_oauth_failures")
        email_dead_letter_total = _count(conn, "SELECT COUNT(*) FROM concerto_email_dead_letter")
        email_dead_letter_last_7d = _count(
            conn,
            "SELECT COUNT(*) FROM concerto_email_dead_letter WHERE attempted_at >= ?",
            week_ago,
        )

        # Stripe webhook activity (real vs test/qa fixtures).
        stripe_events_total = _count(conn, "SELECT COUNT(*) FROM stripe_processed_events")
        stripe_events_real = _count(
            conn,
            "SELECT COUNT(*) FROM stripe_processed_events "
            "WHERE event_id NOT LIKE 'evt_test_%' AND event_id NOT LIKE 'evt_qa_%'",
        )

        # Hosted pool census.
        hosted_pool_active = _count(
            conn,
            "SELECT COUNT(*) FROM concerto_hosted_pool WHERE destroyed_at IS NULL",
        )
        hosted_pool_destroyed = _count(
            conn,
            "SELECT COUNT(*) FROM concerto_hosted_pool WHERE destroyed_at IS NOT NULL",
        )
    finally:
        conn.close()

    return {
        "as_of_ts": now_ts,
        "db_path": _DB_PATH,
        "buyers": {
            "trials_total": trials_total,
            "trials_last_7d": trials_last_7d,
            "paid_total": paid_total,
            "paid_last_7d": paid_last_7d,
            "refunded_total": refunded_total,
        },
        "funnel": {
            "paid_at_set": any_paid,
            "provisioned_at_set": any_provisioned,
            "installed_at_set": any_installed,
            "first_call_at_set": any_first_call,
        },
        "failures": {
            "by_state": failures_by_state,
            "total": sum(failures_by_state.values()),
        },
        "lifecycle": {
            "events_total": lifecycle_events_total,
            "events_last_24h": lifecycle_events_last_24h,
        },
        "reliability": {
            "oauth_failures_total": oauth_failures_total,
            "email_dead_letter_total": email_dead_letter_total,
            "email_dead_letter_last_7d": email_dead_letter_last_7d,
        },
        "stripe": {
            "events_total": stripe_events_total,
            "events_real": stripe_events_real,
        },
        "hosted_pool": {
            "active": hosted_pool_active,
            "destroyed": hosted_pool_destroyed,
        },
    }
