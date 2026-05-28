"""Hosted plan lifecycle reconciler — run hourly via systemd timer.

Reconciles Stripe subscription states against concerto_hosted_pool:
- grace_destroy_at:<ts>: destroy droplet if ts has passed, mark destroyed
- past_due_suspend_at:<ts>: power-off droplet if ts has passed
- reconcile_external_destroys: detect droplets deleted outside Concerto and set destroyed_at
"""
import asyncio
import os
import time

import httpx

from concerto import db, provider_factory as _provider
from concerto.cf_tunnel import destroy_named_tunnel

_CONCERTO_DO_API_TOKEN = os.getenv("CONCERTO_DO_API_TOKEN", "")
_DO_API_BASE = "https://api.digitalocean.com/v2"
_PROVISION_GRACE_SECONDS = 600  # ignore entries created < 10 min ago


async def _do_delete_droplet(droplet_id: str) -> bool:
    # Routed through provider_factory: NF deletes service; DO deletes droplet.
    # Factory destroy_droplet never raises and handles 404 gracefully.
    # CF tunnel cleanup is intentionally kept in the caller (reconcile() below)
    # because the factory would also destroy it — this avoids double-destroy.
    # Returns True (best-effort; factory swallows errors per contract).
    if not droplet_id:
        return False
    await _provider.destroy_droplet(
        api_key=_CONCERTO_DO_API_TOKEN, vps_id=droplet_id, cf_tunnel_id="",
    )
    return True


async def _do_power_off_droplet(droplet_id: str) -> bool:
    # Routed through provider_factory: NF pauses service; DO powers off droplet.
    if not _CONCERTO_DO_API_TOKEN or not droplet_id:
        return False
    await _provider.suspend(api_key=_CONCERTO_DO_API_TOKEN, vps_id=droplet_id)
    return True


async def _list_do_droplet_ids(api_key: str) -> set[str] | None:
    """Fetch all live DO droplet IDs (paginated). Returns None if the API call fails."""
    if not api_key:
        return None
    ids: set[str] = set()
    page = 1
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            while True:
                resp = await client.get(
                    f"{_DO_API_BASE}/droplets",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"page": page, "per_page": 100},
                )
                resp.raise_for_status()
                data = resp.json()
                for d in data.get("droplets", []):
                    ids.add(str(d["id"]))
                if len(data.get("droplets", [])) < 100:
                    break
                page += 1
        return ids
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("DO list droplets failed: %s", exc)
        return None


async def reconcile_external_destroys(dry_run: bool = False) -> dict:
    """Detect droplets deleted outside Concerto and update destroyed_at.

    Safe-by-default: if the DO API call fails, nothing is touched.
    A 10-minute grace period prevents false positives for newly-provisioned entries.
    """
    now = int(time.time())
    reconciled = 0
    skipped = 0
    errors = []

    live_ids = await _list_do_droplet_ids(_CONCERTO_DO_API_TOKEN)
    if live_ids is None:
        return {"reconciled": 0, "skipped": 0, "errors": ["do_api_unavailable"], "dry_run": dry_run}

    entries = await db.get_hosted_pool_entries()

    for entry in entries:
        droplet_id = entry["droplet_id"]
        buyer_token = entry["buyer_token"]
        status = entry["status"]
        created_at = entry.get("created_at", 0) or 0

        if status == "destroyed":
            continue

        # Grace window: newly-provisioned droplet may not appear in DO list yet
        if now - created_at < _PROVISION_GRACE_SECONDS:
            skipped += 1
            continue

        if droplet_id in live_ids:
            continue

        import logging
        logging.getLogger(__name__).info(
            "External destroy detected%s: droplet_id=%s buyer_token=%.8s status=%s",
            " (dry_run)" if dry_run else "", droplet_id, buyer_token, status,
        )

        if dry_run:
            reconciled += 1
            continue

        try:
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
            reconciled += 1
        except Exception as exc:
            errors.append(f"reconcile_failed:{droplet_id}:{exc}")

    return {"reconciled": reconciled, "skipped": skipped, "errors": errors, "dry_run": dry_run}


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
                    # Notify the customer their workspace is paused (recoverable)
                    try:
                        buyer_row = await db.get_buyer(buyer_token)
                        cust_email = (buyer_row or {}).get("email") or ""
                        if cust_email:
                            from concerto.email_templates import payment_issue_suspended
                            from concerto.email_utils import send_email, send_operator_alert
                            billing_url = f"https://concerto.run/dashboard/{buyer_token}"
                            t = payment_issue_suspended(billing_url=billing_url, email=cust_email)
                            await send_email(cust_email, t["subject"], t["html"] or t["text"])
                            await send_operator_alert(
                                "Workspace paused (payment failed)",
                                f"Customer: {cust_email}\nToken: {buyer_token}\nDroplet: {droplet_id}",
                            )
                    except Exception as _e:
                        errors.append(f"suspend_email_failed:{droplet_id}:{_e}")
                else:
                    errors.append(f"poweroff_failed:{droplet_id}")

    ext = await reconcile_external_destroys()
    return {
        "destroyed": destroyed,
        "suspended": suspended,
        "errors": errors,
        "external_reconciled": ext["reconciled"],
        "external_errors": ext["errors"],
    }


if __name__ == "__main__":
    import json
    import sys
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        result = asyncio.run(reconcile_external_destroys(dry_run=True))
    else:
        result = asyncio.run(reconcile())
    print(json.dumps(result))
