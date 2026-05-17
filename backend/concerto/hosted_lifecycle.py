"""Hosted plan lifecycle reconciler — run hourly via systemd timer.

Reconciles Stripe subscription states against concerto_hosted_pool:
- grace_destroy_at:<ts>: destroy droplet if ts has passed, mark destroyed
- past_due_suspend_at:<ts>: power-off droplet if ts has passed
"""
import asyncio
import os
import time

import httpx

from concerto import db
from concerto.cf_tunnel import destroy_named_tunnel

_DO_API_BASE = "https://api.digitalocean.com/v2"
_CONCERTO_DO_API_TOKEN = os.getenv("CONCERTO_DO_API_TOKEN", "")


async def _do_delete_droplet(droplet_id: str) -> bool:
    if not _CONCERTO_DO_API_TOKEN:
        return False
    headers = {"Authorization": f"Bearer {_CONCERTO_DO_API_TOKEN}"}
    async with httpx.AsyncClient(base_url=_DO_API_BASE, headers=headers, timeout=15) as client:
        resp = await client.delete(f"/droplets/{droplet_id}")
        return resp.status_code in (204, 404)


async def _do_power_off_droplet(droplet_id: str) -> bool:
    if not _CONCERTO_DO_API_TOKEN:
        return False
    headers = {
        "Authorization": f"Bearer {_CONCERTO_DO_API_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(base_url=_DO_API_BASE, headers=headers, timeout=15) as client:
        resp = await client.post(
            f"/droplets/{droplet_id}/actions",
            json={"type": "power_off"},
        )
        return resp.status_code in (200, 201)


async def reconcile() -> dict:
    now = int(time.time())
    destroyed = 0
    suspended = 0
    errors = []

    entries = await db.get_hosted_pool_entries()

    for entry in entries:
        status = entry["status"]
        droplet_id = entry["droplet_id"]
        buyer_token = entry["buyer_token"]

        if status.startswith("grace_destroy_at:"):
            try:
                destroy_at = int(status.split(":", 1)[1])
            except ValueError:
                continue
            if now >= destroy_at:
                ok = await _do_delete_droplet(droplet_id)
                if ok:
                    # Destroy associated CF tunnel (Bug #23)
                    buyer_row = await db.get_buyer(buyer_token)
                    cf_tunnel_id = (buyer_row or {}).get("cf_tunnel_id") or ""
                    if cf_tunnel_id:
                        try:
                            await destroy_named_tunnel(cf_tunnel_id)
                        except Exception:
                            pass
                    destroyed += 1
                    # Mark destroyed
                    def _mark(did=droplet_id, ts=now):
                        import sqlite3
                        conn = sqlite3.connect(
                            os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db"),
                            timeout=10,
                        )
                        try:
                            conn.execute(
                                "UPDATE concerto_hosted_pool SET status='destroyed', destroyed_at=? WHERE droplet_id=?",
                                (ts, did),
                            )
                            conn.commit()
                        finally:
                            conn.close()

                    await asyncio.to_thread(_mark)
                    await db.update_buyer(buyer_token, status="expired")
                else:
                    errors.append(f"delete_failed:{droplet_id}")

        elif status.startswith("past_due_suspend_at:"):
            try:
                suspend_at = int(status.split(":", 1)[1])
            except ValueError:
                continue
            if now >= suspend_at:
                ok = await _do_power_off_droplet(droplet_id)
                if ok:
                    suspended += 1
                    await db.update_hosted_pool_status(droplet_id, "suspended")
                    await db.update_buyer(buyer_token, status="suspended")
                else:
                    errors.append(f"poweroff_failed:{droplet_id}")

    return {"destroyed": destroyed, "suspended": suspended, "errors": errors}


if __name__ == "__main__":
    import json
    result = asyncio.run(reconcile())
    print(json.dumps(result))
