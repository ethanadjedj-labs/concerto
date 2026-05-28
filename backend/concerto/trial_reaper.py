"""
Trial reaper — called every 60 s by concerto-trial-reaper.timer.

Finds expired trial buyers (plan='trial', expires_at < now, status not already expired),
destroys their DigitalOcean droplets, marks them expired, and sends the trial_expired email.

Run standalone:
    /opt/concerto/backend/.venv/bin/python -m concerto.trial_reaper
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH       = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
DO_API_TOKEN  = os.getenv("CONCERTO_DO_API_TOKEN", "")
FRONTEND_URL  = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")


# ─── DB ──────────────────────────────────────────────────────────────────────


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _find_expired_trials() -> list[dict]:
    now = int(time.time())
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT token, email, vps_id, vps_ip, expires_at, paid_at, cf_tunnel_id
               FROM concerto_buyers
               WHERE plan = 'trial'
                 AND expires_at < ?
                 AND status NOT IN ('trial_expired', 'trial_upgraded')""",
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# Trials longer than ~31 min are the 48h trials (the 30min trial gets no
# pre-warning, per product decision). Window: <= 2h10 left and not yet warned.
_PRE_WARN_WINDOW_S = 2 * 60 * 60 + 600  # 2h10 (cushion over the 60s timer)
_MIN_LONG_TRIAL_S  = 31 * 60


def _find_pre_expiry_warnings() -> list[dict]:
    now = int(time.time())
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT token, email, expires_at, paid_at
               FROM concerto_buyers
               WHERE plan = 'trial'
                 AND status NOT IN ('trial_expired', 'trial_upgraded')
                 AND pre_expiry_warned_at IS NULL
                 AND expires_at > ?
                 AND expires_at - paid_at > ?
                 AND expires_at - ? <= ?""",
            (now, _MIN_LONG_TRIAL_S, now, _PRE_WARN_WINDOW_S),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _mark_pre_warned(token: str) -> None:
    conn = _conn()
    try:
        conn.execute(
            "UPDATE concerto_buyers SET pre_expiry_warned_at = ? WHERE token = ?",
            (int(time.time()), token),
        )
        conn.commit()
    finally:
        conn.close()


async def _send_pre_expiry_email(email: str, token: str) -> None:
    if not email:
        return
    try:
        from concerto.email_templates import pre_expiry_warning
        from concerto.transactional import get_client
        # has_github: check the buyer row
        conn = _conn()
        try:
            row = conn.execute(
                "SELECT github_token FROM concerto_buyers WHERE token = ?",
                (token,),
            ).fetchone()
        finally:
            conn.close()
        has_gh = bool(row and row["github_token"])
        dash = f"{FRONTEND_URL}/dashboard/{token}"
        tpl = pre_expiry_warning(dashboard_url=dash, email=email,
                                 has_github=has_gh, context="trial")
        html = tpl.get("html") or tpl["text"].replace("\n", "<br>")
        await get_client().send_async(email, tpl["subject"], html, tpl.get("text"))
    except Exception as exc:
        logger.warning("Pre-expiry email to %s failed: %s", email, exc)


def _mark_expired(token: str) -> None:
    conn = _conn()
    try:
        conn.execute(
            "UPDATE concerto_buyers SET status = 'trial_expired' WHERE token = ?",
            (token,),
        )
        conn.commit()
    finally:
        conn.close()


# ─── Droplet + CF tunnel destroy — routed through provider_factory ────────────


async def _destroy_droplet(droplet_id: str, cf_tunnel_id: str = "") -> None:
    # provider_factory selects DO or NF based on CONCERTO_PROVISIONER env var.
    # Factory destroy_droplet: never raises, handles CF tunnel cleanup internally.
    from concerto.provider_factory import destroy_droplet as _factory_destroy
    await _factory_destroy(
        api_key=DO_API_TOKEN,
        vps_id=droplet_id,
        cf_tunnel_id=cf_tunnel_id,
    )


# ─── Email ────────────────────────────────────────────────────────────────────


def _trial_duration_label(expires_at: int, paid_at: int) -> str:
    """Return a human-readable duration label for the trial_expired email."""
    secs = max(0, expires_at - paid_at)
    if secs <= 31 * 60:
        return "30-minute"
    if secs >= 40 * 3600:
        return "48-hour"
    return f"{round(secs / 3600)}-hour"


async def _send_expired_email(email: str, token: str, expires_at: int = 0, paid_at: int = 0) -> None:
    if not email:
        return
    try:

        from concerto.email_templates import trial_expired
        from concerto.transactional import get_client

        upgrade_url = f"{FRONTEND_URL}/upgrade/{token}"
        duration_label = _trial_duration_label(expires_at, paid_at)
        tpl = trial_expired(upgrade_url=upgrade_url, email=email, duration_label=duration_label)
        html = tpl.get("html") or tpl["text"].replace("\n", "<br>")
        await get_client().send_async(email, tpl["subject"], html, tpl.get("text"))
    except Exception as exc:
        logger.warning("Failed to send trial_expired email to %s: %s", email, exc)


# ─── Main ─────────────────────────────────────────────────────────────────────


async def _reap_once() -> int:
    # Pre-expiry warnings for 48h trials (~2h before end) -- send once each.
    warn = _find_pre_expiry_warnings()
    if warn:
        logger.info("Pre-expiry warning for %d trial(s)", len(warn))
        for b in warn:
            _mark_pre_warned(b["token"])
        await asyncio.gather(
            *[_send_pre_expiry_email(b.get("email") or "", b["token"]) for b in warn],
            return_exceptions=True,
        )

    expired = _find_expired_trials()
    if not expired:
        return len(warn) if warn else 0

    logger.info("Reaping %d expired trial(s)", len(expired))
    tasks = []
    for buyer in expired:
        token      = buyer["token"]
        droplet_id = buyer.get("vps_id") or ""
        email      = buyer.get("email") or ""
        cf_tunnel  = buyer.get("cf_tunnel_id") or ""

        logger.info("Reaping trial token=%.8s droplet=%s cf_tunnel=%s email=%s",
                    token, droplet_id, cf_tunnel or "none", email)

        # Mark expired first so double-runs are safe
        _mark_expired(token)

        tasks.append(_destroy_droplet(droplet_id, cf_tunnel))
        tasks.append(_send_expired_email(
            email, token,
            expires_at=buyer.get("expires_at") or 0,
            paid_at=buyer.get("paid_at") or 0,
        ))

    await asyncio.gather(*tasks, return_exceptions=True)
    return len(expired)


def main() -> None:
    reaped = asyncio.run(_reap_once())
    logger.info("Trial reaper done. Reaped: %d", reaped)


if __name__ == "__main__":
    main()
