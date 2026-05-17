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
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(_run)


async def insert_buyer(token: str, email: str, stripe_session_id: str, paid_at: int) -> None:
    def _run():
        conn = _conn()
        try:
            conn.execute(
                """INSERT INTO maestro_buyers (token, email, stripe_session_id, status, paid_at)
                   VALUES (?, ?, ?, 'paid_unprovisioned', ?)""",
                (token, email, stripe_session_id, paid_at),
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
