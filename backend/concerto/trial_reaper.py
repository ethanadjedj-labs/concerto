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
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH       = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
DO_API_TOKEN  = os.getenv("CONCERTO_DO_API_TOKEN", "")
FRONTEND_URL  = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")
DO_API_BASE   = "https://api.digitalocean.com/v2"

_EMAILS_DIR = Path(__file__).parent.parent.parent / "emails"


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


# ─── DO droplet + CF tunnel destroy ──────────────────────────────────────────


async def _destroy_droplet(droplet_id: str, cf_tunnel_id: str = "") -> None:
    if not DO_API_TOKEN or not droplet_id:
        return
    headers = {
        "Authorization": f"Bearer {DO_API_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(base_url=DO_API_BASE, headers=headers, timeout=15) as client:
            resp = await client.delete(f"/droplets/{droplet_id}")
            if resp.status_code not in (204, 404):
                logger.warning("DO destroy %s returned %s", droplet_id, resp.status_code)
    except Exception as exc:
        logger.warning("DO destroy %s failed: %s", droplet_id, exc)

    if cf_tunnel_id:
        from concerto.cf_tunnel import destroy_named_tunnel
        await destroy_named_tunnel(cf_tunnel_id)


# ─── Email ────────────────────────────────────────────────────────────────────


async def _send_expired_email(email: str, token: str) -> None:
    if not email:
        return
    try:
        import sys
        sys.path.insert(0, str(_EMAILS_DIR.parent))
        from emails.transactional import trial_expired
        from concerto.transactional import get_client

        upgrade_url = f"{FRONTEND_URL}/upgrade/{token}"
        tpl = trial_expired(upgrade_url=upgrade_url, email=email)
        html = tpl.get("html") or tpl["text"].replace("\n", "<br>")
        await get_client().send_async(email, tpl["subject"], html, tpl.get("text"))
    except Exception as exc:
        logger.warning("Failed to send trial_expired email to %s: %s", email, exc)


# ─── Main ─────────────────────────────────────────────────────────────────────


async def _reap_once() -> int:
    expired = _find_expired_trials()
    if not expired:
        return 0

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
        tasks.append(_send_expired_email(email, token))

    await asyncio.gather(*tasks, return_exceptions=True)
    return len(expired)


def main() -> None:
    reaped = asyncio.run(_reap_once())
    logger.info("Trial reaper done. Reaped: %d", reaped)


if __name__ == "__main__":
    main()
