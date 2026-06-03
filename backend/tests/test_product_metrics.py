"""
Tests for /api/admin/product-metrics — verify the endpoint returns
counts that come straight out of the SQLite tables (no fabrication, no
in-memory drift).

Strategy: build a throw-away DB seeded with a known set of rows, point
the router at it via CONCERTO_DB_PATH + CONCERTO_OPS_TOKEN, hit the
endpoint with TestClient, then assert every counter matches the seeded
truth.
"""

import importlib
import os
import sqlite3
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


_MIGRATIONS = [
    "001_init.sql",
    "002_ttyd_credentials.sql",
    "003_hosted_plan.sql",
    "004_operator_kit.sql",
    "005_stripe_customer_id.sql",
    "006_drip_tracking.sql",
    "007_recovery.sql",
    "007_pricing_tiers_v2.sql",
    "008_rename_maestro_to_concerto.sql",
    "009_trial_mode.sql",
    "010_email_dead_letter.sql",
    "012_plan_check_solo_pro.sql",
    "013_cf_tunnel_tracking.sql",
    "014_stripe_customer_id_index.sql",
    "015_github_token.sql",
    "016_pre_expiry_warned_at.sql",
    "017_auto_pause.sql",
    "018_callback_secret.sql",
    "019_github_concerto_repo.sql",
    "020_lifecycle_events.sql",
    "021_github_login.sql",
    "022_stripe_event_amounts.sql",
]


def _migrations_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "migrations")


def _apply(conn: sqlite3.Connection, fname: str) -> None:
    with open(os.path.join(_migrations_dir(), fname)) as f:
        sql = f.read()
    for stmt in (s.strip() for s in sql.split(";") if s.strip()):
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "duplicate column name" in msg or "no such table" in msg:
                continue
            raise
    conn.commit()


def _seed_db(path: str) -> None:
    conn = sqlite3.connect(path)
    for m in _MIGRATIONS:
        _apply(conn, m)

    # Two trial rows; one of them fully funneled through first_call.
    conn.execute(
        "INSERT INTO concerto_buyers(token,email,plan,status,paid_at,"
        "provisioned_at,installed_at,first_call_at) "
        "VALUES('t-funneled','a@example.com','trial','trial_expired',"
        "1779000000,1779000050,1779000060,1779000700)"
    )
    conn.execute(
        "INSERT INTO concerto_buyers(token,email,plan,status,paid_at) "
        "VALUES('t-paid-only','b@example.com','trial','paid_unprovisioned',1779000100)"
    )
    # One paid solo customer in a failure state.
    conn.execute(
        "INSERT INTO concerto_buyers(token,email,plan,status,paid_at,failure_reason) "
        "VALUES('p-failed','c@example.com','solo','provisioning_failed',1779000200,'boom')"
    )
    # One refunded buyer.
    conn.execute(
        "INSERT INTO concerto_buyers(token,email,plan,status,paid_at,refunded_at) "
        "VALUES('p-refunded','d@example.com','solo','refunded',1779000300,1779000400)"
    )

    # Lifecycle events tied to the funneled trial.
    conn.execute(
        "INSERT INTO concerto_lifecycle_events(ts,event_type,buyer_token,source) "
        "VALUES(1779000800,'pause','t-funneled','auto_pause')"
    )
    conn.execute(
        "INSERT INTO concerto_lifecycle_events(ts,event_type,buyer_token,source) "
        "VALUES(1779000900,'resume','t-funneled','mcp_proxy_wake')"
    )

    # Stripe events: 1 real, 2 test/qa fixtures.
    conn.execute(
        "INSERT INTO stripe_processed_events(event_id,event_type,processed_at,status) "
        "VALUES('evt_real_001','checkout.session.completed',1779000000,'done')"
    )
    conn.execute(
        "INSERT INTO stripe_processed_events(event_id,event_type,processed_at,status) "
        "VALUES('evt_test_solo_e2e_1','checkout.session.completed',1779000010,'done')"
    )
    conn.execute(
        "INSERT INTO stripe_processed_events(event_id,event_type,processed_at,status) "
        "VALUES('evt_qa_pro_1','checkout.session.completed',1779000020,'done')"
    )

    # One destroyed hosted droplet, one active.
    conn.execute(
        "INSERT INTO concerto_hosted_pool(droplet_id,buyer_token,status,created_at) "
        "VALUES('drop-active','t-funneled','active',1779000000)"
    )
    conn.execute(
        "INSERT INTO concerto_hosted_pool(droplet_id,buyer_token,status,"
        "created_at,destroyed_at) "
        "VALUES('drop-dead','p-failed','destroyed',1778000000,1778900000)"
    )

    # One dead-letter email.
    conn.execute(
        "INSERT INTO concerto_email_dead_letter(to_addr,subject,error,attempted_at) "
        "VALUES('x@test.com','Welcome','smtp 421',1779000000)"
    )

    conn.commit()
    conn.close()


@pytest.fixture
def client():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    _seed_db(tmp.name)

    os.environ["CONCERTO_DB_PATH"] = tmp.name
    os.environ["CONCERTO_OPS_TOKEN"] = "test-ops-token-xyz"

    # Reimport with the env vars set so the module-level constants pick them up.
    import concerto.product_metrics_router as pm
    importlib.reload(pm)

    app = FastAPI()
    app.include_router(pm.router)
    yield TestClient(app)

    os.unlink(tmp.name)


def test_requires_bearer_token(client):
    r = client.get("/api/admin/product-metrics")
    assert r.status_code == 401


def test_rejects_wrong_token(client):
    r = client.get(
        "/api/admin/product-metrics",
        headers={"Authorization": "Bearer wrong"},
    )
    assert r.status_code == 401


def test_returns_honest_counts(client):
    r = client.get(
        "/api/admin/product-metrics",
        headers={"Authorization": "Bearer test-ops-token-xyz"},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # Buyers: 2 trials, 2 paid (solo), 1 refunded.
    assert body["buyers"]["trials_total"] == 2
    assert body["buyers"]["paid_total"] == 2
    assert body["buyers"]["refunded_total"] == 1

    # Funnel: paid_at set on all 4 rows; only t-funneled has the full set.
    assert body["funnel"]["paid_at_set"] == 4
    assert body["funnel"]["provisioned_at_set"] == 1
    assert body["funnel"]["installed_at_set"] == 1
    assert body["funnel"]["first_call_at_set"] == 1

    # Failures: 1 in provisioning_failed.
    assert body["failures"]["by_state"] == {"provisioning_failed": 1}
    assert body["failures"]["total"] == 1

    # Lifecycle: 2 events total.
    assert body["lifecycle"]["events_total"] == 2

    # Stripe: 3 total, 1 real (the others are test/qa fixtures).
    assert body["stripe"]["events_total"] == 3
    assert body["stripe"]["events_real"] == 1

    # Hosted pool: 1 active, 1 destroyed.
    assert body["hosted_pool"]["active"] == 1
    assert body["hosted_pool"]["destroyed"] == 1

    # Reliability: 1 dead-letter email.
    assert body["reliability"]["email_dead_letter_total"] == 1
    assert body["reliability"]["oauth_failures_total"] == 0


def test_empty_db_returns_all_zeros(tmp_path, monkeypatch):
    """When the DB is freshly migrated with no rows, every counter must be 0."""
    db_path = str(tmp_path / "empty.db")
    conn = sqlite3.connect(db_path)
    for m in _MIGRATIONS:
        _apply(conn, m)
    conn.close()

    monkeypatch.setenv("CONCERTO_DB_PATH", db_path)
    monkeypatch.setenv("CONCERTO_OPS_TOKEN", "tok")

    import concerto.product_metrics_router as pm
    importlib.reload(pm)

    app = FastAPI()
    app.include_router(pm.router)
    with TestClient(app) as c:
        r = c.get(
            "/api/admin/product-metrics",
            headers={"Authorization": "Bearer tok"},
        )
        assert r.status_code == 200
        body = r.json()
        for section in ("buyers", "funnel", "failures", "lifecycle",
                        "reliability", "stripe", "hosted_pool"):
            for v in body[section].values():
                if isinstance(v, int):
                    assert v == 0, f"{section} counter not zero on empty DB: {body[section]}"
                elif isinstance(v, dict):
                    assert v == {}, f"{section} dict counter not empty: {v}"
