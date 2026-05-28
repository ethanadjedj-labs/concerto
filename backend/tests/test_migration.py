"""Smoke-test the migration SQL files."""
import os
import sqlite3
import tempfile


def _migrations_dir():
    return os.path.join(os.path.dirname(__file__), "..", "migrations")


def _apply_migration_idempotent(conn: sqlite3.Connection, filename: str) -> None:
    """Mirror db.run_migration(): execute statements one-by-one, skip duplicate columns."""
    path = os.path.join(_migrations_dir(), filename)
    with open(path) as f:
        sql = f.read()
    for stmt in (s.strip() for s in sql.split(";") if s.strip()):
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise
    conn.commit()


def test_001_init_creates_table():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration_idempotent(conn, "001_init.sql")
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='concerto_buyers'"
        ).fetchall()
        assert rows, "concerto_buyers table not created by 001_init.sql"
        conn.close()


def test_002_adds_ttyd_columns():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration_idempotent(conn, "001_init.sql")
        _apply_migration_idempotent(conn, "002_ttyd_credentials.sql")

        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(concerto_buyers)").fetchall()
        }
        assert "ttyd_password" in cols, "ttyd_password column missing after migration 002"
        assert "ttyd_public_url" in cols, "ttyd_public_url column missing after migration 002"
        conn.close()


def test_002_is_idempotent():
    """Running migration 002 twice must not raise (duplicate column silenced)."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration_idempotent(conn, "001_init.sql")
        _apply_migration_idempotent(conn, "002_ttyd_credentials.sql")
        _apply_migration_idempotent(conn, "002_ttyd_credentials.sql")  # second run must not raise
        conn.close()


def test_014_stripe_customer_id_index():
    """Migration 014 must create idx_concerto_buyers_stripe_customer_id."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration_idempotent(conn, "001_init.sql")
        _apply_migration_idempotent(conn, "005_stripe_customer_id.sql")
        _apply_migration_idempotent(conn, "014_stripe_customer_id_index.sql")
        indexes = {
            row[1]
            for row in conn.execute(
                "SELECT * FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "idx_concerto_buyers_stripe_customer_id" in indexes, (
            "stripe_customer_id index not created by 014_stripe_customer_id_index.sql"
        )
        conn.close()


def test_014_is_idempotent():
    """Migration 014 (CREATE INDEX IF NOT EXISTS) must be safe to run twice."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        _apply_migration_idempotent(conn, "001_init.sql")
        _apply_migration_idempotent(conn, "005_stripe_customer_id.sql")
        _apply_migration_idempotent(conn, "014_stripe_customer_id_index.sql")
        _apply_migration_idempotent(conn, "014_stripe_customer_id_index.sql")
        conn.close()
