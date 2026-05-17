import asyncio
import os
import sqlite3

DB_PATH = os.getenv("MAESTRO_DB_PATH", "/var/lib/maestro/maestro.db")


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


async def run_migration(sql: str) -> None:
    def _run():
        conn = _conn()
        try:
            for stmt in (s.strip() for s in sql.split(";") if s.strip()):
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_run)


async def insert_buyer(token: str, email: str, stripe_session_id: str, paid_at: int) -> None:
    await insert_buyer_with_plan(
        token=token,
        email=email,
        stripe_session_id=stripe_session_id,
        paid_at=paid_at,
        plan="byoc",
    )


async def insert_buyer_with_plan(
    token: str,
    email: str,
    stripe_session_id: str,
    paid_at: int,
    plan: str = "byoc",
    subscription_id: str | None = None,
    subscription_status: str | None = None,
    next_renewal_at: int | None = None,
) -> None:
    def _run():
        conn = _conn()
        try:
            conn.execute(
                """INSERT INTO maestro_buyers
                   (token, email, stripe_session_id, status, paid_at,
                    plan, subscription_id, subscription_status, next_renewal_at)
                   VALUES (?, ?, ?, 'paid_unprovisioned', ?, ?, ?, ?, ?)""",
                (token, email, stripe_session_id, paid_at,
                 plan, subscription_id, subscription_status, next_renewal_at),
            )
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_run)


async def get_buyer(token: str) -> dict | None:
    def _run():
        conn = _conn()
        try:
            row = conn.execute(
                "SELECT * FROM maestro_buyers WHERE token = ?", (token,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    return await asyncio.to_thread(_run)


async def get_buyer_by_subscription(subscription_id: str) -> dict | None:
    def _run():
        conn = _conn()
        try:
            row = conn.execute(
                "SELECT * FROM maestro_buyers WHERE subscription_id = ?",
                (subscription_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    return await asyncio.to_thread(_run)


async def update_buyer(token: str, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [token]

    def _run():
        conn = _conn()
        try:
            conn.execute(
                f"UPDATE maestro_buyers SET {set_clause} WHERE token = ?",
                values,
            )
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_run)


async def upsert_hosted_pool(
    droplet_id: str,
    buyer_token: str,
    ipv4: str | None,
    status: str,
    created_at: int,
) -> None:
    def _run():
        conn = _conn()
        try:
            conn.execute(
                """INSERT INTO maestro_hosted_pool
                   (droplet_id, buyer_token, ipv4, status, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(droplet_id) DO UPDATE SET
                     ipv4 = excluded.ipv4,
                     status = excluded.status""",
                (droplet_id, buyer_token, ipv4, status, created_at),
            )
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_run)


async def update_hosted_pool_status(droplet_id: str, status: str) -> None:
    def _run():
        conn = _conn()
        try:
            conn.execute(
                "UPDATE maestro_hosted_pool SET status = ? WHERE droplet_id = ?",
                (status, droplet_id),
            )
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_run)


async def get_hosted_pool_entries(status_prefix: str | None = None) -> list[dict]:
    def _run():
        conn = _conn()
        try:
            if status_prefix:
                rows = conn.execute(
                    "SELECT * FROM maestro_hosted_pool WHERE status LIKE ?",
                    (f"{status_prefix}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM maestro_hosted_pool WHERE destroyed_at IS NULL"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    return await asyncio.to_thread(_run)
