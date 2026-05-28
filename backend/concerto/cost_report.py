"""CLI report for Concerto auto-pause economic outcomes.

Usage:
    python -m concerto.cost_report                   # last 30 days
    python -m concerto.cost_report --days 7
    python -m concerto.cost_report --month 2026-05
"""
from __future__ import annotations

import argparse
import calendar
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone

DB_PATH = os.getenv("CONCERTO_DB_PATH", "/var/lib/concerto/concerto.db")
_HOURLY_RATE = float(os.getenv("CONCERTO_NF_HOURLY_RATE_USD", "0.012"))


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS concerto_lifecycle_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            buyer_token TEXT NOT NULL,
            vps_id TEXT,
            idle_seconds INTEGER,
            resume_latency_ms INTEGER,
            source TEXT,
            detail TEXT
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_ts ON concerto_lifecycle_events(ts)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_buyer ON concerto_lifecycle_events(buyer_token)"
    )
    conn.commit()


def _compute_paused_seconds(
    conn: sqlite3.Connection, start_ts: int, end_ts: int, now_ts: int
) -> tuple[float, dict[str, float]]:
    """Return (total_seconds, {buyer_token: seconds}) for pauses in the window."""
    pauses = conn.execute(
        """SELECT ts, buyer_token FROM concerto_lifecycle_events
           WHERE event_type = 'pause' AND ts >= ? AND ts < ?
           ORDER BY ts""",
        (start_ts, end_ts),
    ).fetchall()

    user_seconds: dict[str, float] = {}
    for p in pauses:
        token = p["buyer_token"]
        resume = conn.execute(
            """SELECT ts FROM concerto_lifecycle_events
               WHERE event_type = 'resume' AND buyer_token = ? AND ts > ?
               ORDER BY ts LIMIT 1""",
            (token, p["ts"]),
        ).fetchone()
        end = resume["ts"] if resume else now_ts
        user_seconds[token] = user_seconds.get(token, 0) + float(end - p["ts"])

    return sum(user_seconds.values()), user_seconds


def run_report(start_ts: int, end_ts: int, period_label: str) -> None:
    now_ts = int(time.time())
    conn = _conn()
    try:
        _ensure_table(conn)

        pause_count = conn.execute(
            """SELECT COUNT(*) FROM concerto_lifecycle_events
               WHERE event_type = 'pause' AND ts >= ? AND ts < ?""",
            (start_ts, end_ts),
        ).fetchone()[0]

        resume_count = conn.execute(
            """SELECT COUNT(*) FROM concerto_lifecycle_events
               WHERE event_type = 'resume' AND ts >= ? AND ts < ?""",
            (start_ts, end_ts),
        ).fetchone()[0]

        avg_idle = conn.execute(
            """SELECT AVG(idle_seconds) FROM concerto_lifecycle_events
               WHERE event_type = 'pause' AND ts >= ? AND ts < ?
               AND idle_seconds IS NOT NULL""",
            (start_ts, end_ts),
        ).fetchone()[0]

        avg_latency_ms = conn.execute(
            """SELECT AVG(resume_latency_ms) FROM concerto_lifecycle_events
               WHERE event_type = 'resume' AND ts >= ? AND ts < ?
               AND resume_latency_ms IS NOT NULL""",
            (start_ts, end_ts),
        ).fetchone()[0]

        total_secs, user_secs = _compute_paused_seconds(conn, start_ts, end_ts, now_ts)
        total_hours = total_secs / 3600.0
        cost_saved = total_hours * _HOURLY_RATE

        top5 = sorted(user_secs.items(), key=lambda x: x[1], reverse=True)[:5]
        top5_display: list[tuple[str, float]] = []
        for token, secs in top5:
            try:
                row = conn.execute(
                    "SELECT email FROM concerto_buyers WHERE token = ?", (token,)
                ).fetchone()
                label = row["email"] if row else (token[:8] + "...")
            except sqlite3.OperationalError:
                label = token[:8] + "..."
            top5_display.append((label, secs / 3600.0))

    finally:
        conn.close()

    print("Concerto auto-pause cost report")
    print(f"Period: {period_label}")
    print()
    print(f"Pause events:       {pause_count}")
    print(f"Resume events:      {resume_count}")

    if avg_idle is not None:
        print(f"Avg idle before pause:   {avg_idle / 60.0:.0f} min")
    else:
        print("Avg idle before pause:   n/a")

    if avg_latency_ms is not None:
        print(f"Avg resume latency:      {avg_latency_ms / 1000.0:.1f} s")
    else:
        print("Avg resume latency:      n/a")

    print(f"Estimated compute hours paused: {total_hours:.0f} h")
    print(f"Estimated compute saved (NF ${_HOURLY_RATE}/h CPU 2 GiB): ${cost_saved:.2f}")
    print()
    print("Top 5 most-paused users (by hours paused):")
    if top5_display:
        for label, hours in top5_display:
            print(f"  {label:<40} {hours:.0f}h")
    else:
        print("  (no data)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Concerto auto-pause cost report")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--days", type=int, default=None, help="Last N days (default: 30)")
    group.add_argument("--month", type=str, default=None, help="Calendar month, e.g. 2026-05")
    args = parser.parse_args()

    now_ts = int(time.time())
    now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)

    if args.month:
        year, month = map(int, args.month.split("-"))
        start_dt = datetime(year, month, 1, tzinfo=timezone.utc)
        end_dt = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        days = (end_dt - start_dt).days
        start_date = start_dt.date()
        end_date = (end_dt - timedelta(days=1)).date()
        period_label = f"{start_date} to {end_date} ({days} days)"
    else:
        days = args.days if args.days is not None else 30
        end_ts = now_ts
        start_ts = now_ts - days * 86400
        start_date = datetime.fromtimestamp(start_ts, tz=timezone.utc).date()
        end_date = now_dt.date()
        period_label = f"{start_date} to {end_date} ({days} days)"

    run_report(start_ts, end_ts, period_label)


if __name__ == "__main__":
    main()
