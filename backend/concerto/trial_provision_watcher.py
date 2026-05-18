"""
Trial provision watcher — called every 60 s by concerto-trial-provision-watcher.timer.

Finds trial buyers stuck in `installing` state:
  - age > 8 min  → mark provisioning_failed (gives wizard the failure card).
  - 45 s < age < 8 min → SSH-probe the droplet; if ttyd is active and bearer
    token is readable, promote to awaiting_oauth and send the trial_ready email.

The callback path (provision_complete.sh → POST /api/internal/droplet-ready) is
the primary mechanism; this watcher is the fallback for when that POST fails.

Run standalone:
    /opt/concerto/backend/.venv/bin/python -m concerto.trial_provision_watcher
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import sqlite3
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH      = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
FRONTEND_URL = os.getenv("CONCERTO_FRONTEND_URL", "https://concerto.run")

_PROBE_AFTER_S  = 45       # Start SSH-probing after 45 s in installing
_FAIL_AFTER_S   = 1500      # Mark failed after 25 min (cloud-init can take 15-20 min on slow DO)


# ─── DB ──────────────────────────────────────────────────────────────────────


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _find_stuck_trials() -> list[dict]:
    cutoff = int(time.time()) - _PROBE_AFTER_S
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT token, email, vps_id, vps_ip, ssh_keypair_private_path,
                      provisioned_at, expires_at, cf_tunnel_id, plan
               FROM concerto_buyers
               WHERE status = 'installing'
                 AND plan = 'trial'
                 AND provisioned_at < ?""",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _set_failed(token: str, reason: str) -> None:
    conn = _conn()
    try:
        conn.execute(
            "UPDATE concerto_buyers SET status='provisioning_failed', failure_reason=? WHERE token=?",
            (reason, token),
        )
        conn.commit()
    finally:
        conn.close()


def _set_awaiting_oauth(
    token: str, mcp_url: str, bearer_token: str, ttyd_url: str
) -> None:
    conn = _conn()
    try:
        conn.execute(
            """UPDATE concerto_buyers
               SET status='awaiting_oauth', mcp_url=?, bearer_token=?, ttyd_public_url=?,
                   installed_at=?
               WHERE token=? AND status='installing'""",
            (mcp_url, bearer_token, ttyd_url, int(time.time()), token),
        )
        conn.commit()
    finally:
        conn.close()


# ─── SSH probe ────────────────────────────────────────────────────────────────


async def _ssh_probe(vps_ip: str, key_path: str) -> dict | None:
    """
    SSH into the droplet.  Returns dict with 'bearer' and 'tunnel_hostname',
    or None on failure.

    Reads:
      - /etc/concerto/token        (MCP bearer token)
      - TUNNEL_HOSTNAME from /etc/concerto/env
      - systemctl is-active concerto-ttyd
    """
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8",
        "-o", "BatchMode=yes",
        f"root@{vps_ip}",
        (
            "bash -c '"
            "systemctl is-active concerto-ttyd 2>/dev/null; "
            "cat /etc/concerto/token 2>/dev/null || echo MISSING; "
            "grep TUNNEL_HOSTNAME /etc/concerto/env 2>/dev/null | cut -d= -f2; "
            "grep -hoE \"https://[a-z0-9-]+\\.trycloudflare\\.com\" "
            "/var/log/cloudflared-quicktunnel.log /var/log/cloudflared*.log 2>/dev/null "
            "| head -1 || echo';"
        ),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        lines = stdout.decode("utf-8", errors="replace").strip().splitlines()
        if len(lines) < 2:
            return None
        ttyd_active = lines[0].strip() == "active"
        bearer = lines[1].strip()
        tunnel_hostname = lines[2].strip() if len(lines) > 2 else ""
        # 4th line: trycloudflare URL scraped from the cloudflared quick-tunnel log.
        # Empty for named-tunnel trials (which use tunnel run --token, not --url).
        # Kept as fallback for in-flight trials provisioned before the named-tunnel migration.
        real_tunnel_url = lines[3].strip() if len(lines) > 3 else ""
        if not ttyd_active or bearer == "MISSING" or not bearer:
            return None
        return {
            "bearer": bearer,
            "tunnel_hostname": tunnel_hostname,
            "real_tunnel_url": real_tunnel_url,
        }
    except (asyncio.TimeoutError, Exception) as exc:
        logger.debug("SSH probe failed for %s: %s", vps_ip, exc)
        return None


# ─── Promote helper ───────────────────────────────────────────────────────────


async def _promote(buyer: dict, probe: dict) -> None:
    token = buyer["token"]
    tunnel_hostname = probe.get("tunnel_hostname", "")
    real_tunnel_url = probe.get("real_tunnel_url", "")
    # Resolve the MCP URL in priority order:
    #   1. Named-tunnel hostname from TUNNEL_HOSTNAME env (trials and hosted plans both
    #      now provision a named Concerto-domain tunnel, so this is the primary path).
    #   2. The REAL ephemeral trycloudflare URL scraped from the droplet (fallback for
    #      in-flight trials provisioned before the named-tunnel migration).
    # NEVER fabricate a URL that doesn't have a working tunnel behind it.
    if tunnel_hostname:
        mcp_url = f"https://{tunnel_hostname}"
    elif real_tunnel_url:
        mcp_url = real_tunnel_url
    else:
        # No reliable URL yet — do NOT promote with a guessed URL.
        # Leave it to the droplet-ready callback, which carries the real URL.
        logger.info(
            "Skipping SSH-probe promote for %.8s: no tunnel URL yet "
            "(awaiting droplet-ready callback)", token,
        )
        return
    ttyd_url = f"{mcp_url}/terminal"
    bearer   = probe["bearer"]

    _set_awaiting_oauth(token, mcp_url, bearer, ttyd_url)
    logger.info("Promoted token %.8s to awaiting_oauth via SSH probe", token)

    # Send trial_ready email
    try:
        from concerto.email_templates import trial_ready
        from concerto.email_utils import send_email
        email     = buyer.get("email", "")
        dashboard = f"{FRONTEND_URL}/dashboard/{token}"
        expires   = buyer.get("expires_at", 0)
        minutes   = max(1, math.ceil((expires - time.time()) / 60)) if expires else 25
        tpl = trial_ready(dashboard_url=dashboard, email=email, minutes=minutes)
        await send_email(email, tpl["subject"], tpl.get("html") or tpl["text"])
        logger.info("trial_ready email sent to %s", email)
    except Exception:
        logger.exception("trial_ready email failed for token %.8s", token)


# ─── Main ─────────────────────────────────────────────────────────────────────


async def _watch_once() -> int:
    stuck = _find_stuck_trials()
    if not stuck:
        return 0

    logger.info("Watching %d stuck trial(s) in installing", len(stuck))
    now = time.time()
    promoted = 0

    for buyer in stuck:
        token         = buyer["token"]
        provisioned   = buyer.get("provisioned_at") or 0
        age           = now - provisioned
        vps_ip        = buyer.get("vps_ip", "")
        key_path      = buyer.get("ssh_keypair_private_path", "")

        if age >= _FAIL_AFTER_S:
            reason = f"Cloud-init timed out after {int(age)}s without callback"
            _set_failed(token, reason)
            logger.warning("Marked token %.8s provisioning_failed (age=%ds)", token, int(age))
            continue

        if not vps_ip or not key_path or not Path(key_path).exists():
            logger.debug("Skipping token %.8s — no ip/key yet", token)
            continue

        probe = await _ssh_probe(vps_ip, key_path)
        if probe:
            await _promote(buyer, probe)
            promoted += 1
        else:
            logger.debug("SSH probe not ready for token %.8s (age=%ds)", token, int(age))

    return promoted


def main() -> None:
    promoted = asyncio.run(_watch_once())
    logger.info("Trial provision watcher done. Promoted: %d", promoted)


if __name__ == "__main__":
    main()
