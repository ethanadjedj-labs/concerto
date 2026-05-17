"""Maestro monitoring: hourly hosted-pool healthcheck + operator alerting.

Run as a systemd timer (maestro-monitoring.timer) or directly:
    python -m maestro.monitoring
"""
import asyncio
import os
import time

import httpx

from maestro import db
from maestro.email_utils import send_operator_alert

_MANAGER_STATE_PATH = "/opt/cortex/OPS/MANAGER_STATE.md"
_MCP_HEALTHCHECK_TIMEOUT = 10
_ALERT_THRESHOLD = 3


def _get_active_hosted_buyers() -> list[dict]:
    conn = db._conn()
    try:
        rows = conn.execute(
            "SELECT * FROM maestro_buyers WHERE status = 'active' AND provider = 'hosted'"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


async def _check_mcp(mcp_url: str) -> bool:
    if not mcp_url or mcp_url.startswith("stub://") or mcp_url.startswith("tunnel_failed"):
        return False
    try:
        async with httpx.AsyncClient(timeout=_MCP_HEALTHCHECK_TIMEOUT) as client:
            r = await client.get(
                mcp_url.rstrip("/") + "/health",
                follow_redirects=True,
            )
            return r.status_code < 500
    except Exception:
        return False


def _append_manager_state_alert(msg: str) -> None:
    try:
        entry = (
            f"\n\n## ALERT — Maestro Hosted Pool ({time.strftime('%Y-%m-%d %H:%M UTC')})\n\n"
            f"{msg}\n\n"
            "**Action required**: investigate degraded droplets, consider re-provisioning.\n"
        )
        with open(_MANAGER_STATE_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass


async def run_healthcheck() -> dict:
    buyers = _get_active_hosted_buyers()
    if not buyers:
        print(f"[monitoring] No active hosted buyers to check. ts={int(time.time())}")
        return {"checked": 0, "failed": 0}

    results = await asyncio.gather(
        *[_check_mcp(b.get("mcp_url", "")) for b in buyers],
        return_exceptions=True,
    )

    failed = [b for b, ok in zip(buyers, results) if not ok]
    checked = len(buyers)
    now = int(time.time())

    for b in buyers:
        await db.update_buyer(b["token"], last_seen_at=now)

    if len(failed) >= _ALERT_THRESHOLD:
        tokens_preview = [f"{b['token'][:8]}..." for b in failed[:10]]
        msg = (
            f"{len(failed)}/{checked} hosted droplets unreachable.\n"
            f"Affected tokens: {tokens_preview}\n"
            f"Checked at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}"
        )
        await send_operator_alert("Hosted pool degraded", msg)
        _append_manager_state_alert(msg)
        print(f"[monitoring] ALERT sent: {len(failed)}/{checked} failed")
    else:
        print(f"[monitoring] OK: {len(failed)}/{checked} failed (threshold={_ALERT_THRESHOLD})")

    return {"checked": checked, "failed": len(failed)}


async def check_oauth_reminders() -> None:
    """Send reminder emails for buyers who haven't completed setup."""
    conn = db._conn()
    try:
        buyers = [dict(r) for r in conn.execute("SELECT * FROM maestro_buyers").fetchall()]
    finally:
        conn.close()

    now = int(time.time())
    for buyer in buyers:
        email = buyer.get("email", "")
        token = buyer["token"]
        status = buyer.get("status", "")
        paid_at = buyer.get("paid_at") or 0

        if not email or status in ("refunded", "suspended", "active"):
            continue

        hours_since_paid = (now - paid_at) / 3600

        # 24h: customer never opened dashboard
        if (
            status == "awaiting_oauth"
            and not buyer.get("dashboard_opened_at")
            and hours_since_paid >= 24
            and not buyer.get("reminder_24h_sent")
        ):
            from maestro.email_utils import send_email
            setup_url = f"https://maestro.run/dashboard/{token}"
            await send_email(
                to=email,
                subject="Your Maestro is ready — finish setup",
                html=(
                    "<p>Hi,</p>"
                    "<p>Your Maestro remote workspace is ready! "
                    "Click below to access your dashboard and connect Claude:</p>"
                    f'<p><a href="{setup_url}" style="background:#7c3aed;color:white;'
                    f'padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block">'
                    f"Open My Maestro</a></p>"
                    "<p>If you have any questions, reply to this email.</p>"
                ),
            )
            await db.update_buyer(token, reminder_24h_sent=1)

        # 48h: customer opened dashboard but never ran OAuth
        if (
            buyer.get("dashboard_opened_at")
            and status == "awaiting_oauth"
            and hours_since_paid >= 48
            and not buyer.get("reminder_48h_sent")
        ):
            from maestro.email_utils import send_email
            await send_email(
                to=email,
                subject="Need help with the Claude OAuth step?",
                html=(
                    "<p>Hi,</p>"
                    "<p>We noticed you opened your Maestro dashboard but haven't "
                    "completed the Claude OAuth step yet.</p>"
                    "<p>In your terminal, run:</p>"
                    "<pre style='background:#1a1a1a;color:#fff;padding:12px;border-radius:6px'>"
                    "claude auth login</pre>"
                    "<p>A browser window will open — log in to your Claude account. "
                    "That's it!</p>"
                    "<p>Reply to this email or contact "
                    "<a href='mailto:support@maestro.run'>support@maestro.run</a> "
                    "if you need help.</p>"
                ),
            )
            await db.update_buyer(token, reminder_48h_sent=1)


if __name__ == "__main__":
    async def _main():
        hc = await run_healthcheck()
        await check_oauth_reminders()
        print(f"Done: {hc}")

    asyncio.run(_main())
