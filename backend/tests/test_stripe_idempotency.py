"""Tests for commit-after-success Stripe idempotency + amount recording.

Runs against a throwaway scratch DB (CONCERTO_DB_PATH points at a tempfile,
set BEFORE importing concerto.db so DB_PATH binds to it). All Stripe + DO +
email side effects are mocked — zero live external calls, never the live DB.

Contract under test:
  * a handler that raises does NOT mark the event processed (Stripe can retry)
  * a successful handler marks the event 'done' exactly once (retries dedupe)
  * paid amount + currency are recorded on the event and the buyer
  * concurrent duplicate delivery is told to retry (409), stale claims reclaim
"""
import os
import sqlite3
import tempfile
import time

import pytest

# ── Scratch DB wiring — MUST precede any concerto import ──────────────────────
_SCRATCH_DIR = tempfile.mkdtemp(prefix="concerto-stripe-idem-")
_SCRATCH_DB = os.path.join(_SCRATCH_DIR, "scratch.db")
os.environ["CONCERTO_DB_PATH"] = _SCRATCH_DB
os.environ.setdefault("STRIPE_CONCERTO_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")

from fastapi import HTTPException  # noqa: E402

from concerto import db  # noqa: E402
from concerto import stripe_webhook as sw  # noqa: E402

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


def _apply_all_migrations() -> None:
    conn = sqlite3.connect(_SCRATCH_DB)
    try:
        for fname in _MIGRATIONS:
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
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    # Bind to the scratch DB per-test (monkeypatch auto-restores afterward, so
    # this never leaks into other test modules). db._conn() reads DB_PATH at
    # call time, making this authoritative regardless of import order — and a
    # hard guarantee that we never touch the live DB.
    monkeypatch.setattr(db, "DB_PATH", _SCRATCH_DB)
    monkeypatch.setattr(sw, "_WEBHOOK_SECRET", "whsec_test")
    assert db.DB_PATH == _SCRATCH_DB and db.DB_PATH != "/var/lib/concerto/concerto.db"

    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(_SCRATCH_DB + suffix)
        except FileNotFoundError:
            pass
    _apply_all_migrations()
    yield


# ── Helpers ──────────────────────────────────────────────────────────────────


def _events() -> list[dict]:
    conn = sqlite3.connect(_SCRATCH_DB)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM stripe_processed_events"
        ).fetchall()]
    finally:
        conn.close()


def _buyers() -> list[dict]:
    conn = sqlite3.connect(_SCRATCH_DB)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM concerto_buyers"
        ).fetchall()]
    finally:
        conn.close()


class _FakeRequest:
    headers = {"stripe-signature": "sig_test"}

    async def body(self) -> bytes:
        return b"{}"


def _patch_event(monkeypatch, event: dict) -> None:
    monkeypatch.setattr(sw.stripe.Webhook, "construct_event", lambda *a, **k: event)


# ── _claim_event / _mark_done / _release_event unit tests ─────────────────────


def test_claim_lifecycle_new_busy_done_duplicate():
    assert sw._claim_event("evt_1", "invoice.paid") == sw._CLAIM_NEW
    # A second delivery while the first is still 'processing' must not re-run.
    assert sw._claim_event("evt_1", "invoice.paid") == sw._CLAIM_BUSY

    sw._mark_done("evt_1", 2900, "usd")
    # Once 'done', further deliveries dedupe.
    assert sw._claim_event("evt_1", "invoice.paid") == sw._CLAIM_DONE

    row = _events()[0]
    assert row["status"] == "done"
    assert row["amount"] == 2900
    assert row["currency"] == "usd"


def test_stale_processing_is_reclaimed():
    old = int(time.time()) - (sw._STALE_PROCESSING_SECONDS + 10)
    conn = sqlite3.connect(_SCRATCH_DB)
    conn.execute(
        "INSERT INTO stripe_processed_events "
        "(event_id, event_type, status, processed_at, received_at, claimed_at) "
        "VALUES (?, ?, 'processing', 0, ?, ?)",
        ("evt_stale", "invoice.paid", old, old),
    )
    conn.commit()
    conn.close()
    # Abandoned claim past the staleness window must be reclaimable.
    assert sw._claim_event("evt_stale", "invoice.paid") == sw._CLAIM_NEW


def test_release_never_removes_done():
    sw._claim_event("evt_done", "invoice.paid")
    sw._mark_done("evt_done", 100, "usd")
    sw._release_event("evt_done")  # must be a no-op for completed events
    rows = _events()
    assert len(rows) == 1
    assert rows[0]["status"] == "done"


def test_release_removes_processing_claim():
    sw._claim_event("evt_tmp", "invoice.paid")
    sw._release_event("evt_tmp")
    assert _events() == []


# ── Endpoint: ordering contract ───────────────────────────────────────────────


async def test_handler_raises_does_not_mark_processed(monkeypatch):
    _patch_event(monkeypatch, {
        "id": "evt_fail", "type": "invoice.paid", "data": {"object": {}},
    })

    async def boom(*_a, **_k):
        raise RuntimeError("handler exploded after partial work")

    monkeypatch.setattr(sw, "_dispatch_event", boom)

    with pytest.raises(RuntimeError):
        await sw.stripe_webhook(_FakeRequest())

    # Claim was released — nothing marked done, so Stripe's retry can reprocess.
    assert _events() == []
    assert sw._claim_event("evt_fail", "invoice.paid") == sw._CLAIM_NEW


async def test_success_marks_once_and_retry_dedupes(monkeypatch):
    _patch_event(monkeypatch, {
        "id": "evt_ok", "type": "invoice.paid", "data": {"object": {}},
    })
    calls = {"n": 0}

    async def disp(event_type, _obj, _md):
        calls["n"] += 1
        return {"received": True, "event_type": event_type}, 4900, "usd"

    monkeypatch.setattr(sw, "_dispatch_event", disp)

    first = await sw.stripe_webhook(_FakeRequest())
    assert first == {"received": True, "event_type": "invoice.paid"}

    second = await sw.stripe_webhook(_FakeRequest())
    assert second == {"ignored": True, "reason": "duplicate event"}

    assert calls["n"] == 1  # handler ran exactly once
    rows = _events()
    assert len(rows) == 1
    assert rows[0]["status"] == "done"
    assert rows[0]["amount"] == 4900
    assert rows[0]["currency"] == "usd"


async def test_concurrent_delivery_returns_409(monkeypatch):
    # Simulate a first delivery still in flight (fresh 'processing' claim).
    assert sw._claim_event("evt_busy", "invoice.paid") == sw._CLAIM_NEW

    _patch_event(monkeypatch, {
        "id": "evt_busy", "type": "invoice.paid", "data": {"object": {}},
    })

    async def disp(*_a, **_k):  # must never run for an in-flight duplicate
        raise AssertionError("dispatch ran for a concurrent duplicate")

    monkeypatch.setattr(sw, "_dispatch_event", disp)

    with pytest.raises(HTTPException) as excinfo:
        await sw.stripe_webhook(_FakeRequest())
    assert excinfo.value.status_code == 409


# ── Endpoint: amount recording (real dispatch, mocked side effects) ────────────


async def test_checkout_records_amount_and_currency(monkeypatch):
    async def _noop_email(*_a, **_k):
        return None

    monkeypatch.setattr(sw, "send_email", _noop_email)
    monkeypatch.setattr("concerto.drip_runner.send_immediate_drip", lambda *_a, **_k: None)

    _patch_event(monkeypatch, {
        "id": "evt_checkout",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_123",
            "amount_total": 2900,
            "currency": "usd",
            "customer": "cus_123",
            "metadata": {"product": "concerto", "plan": "solo"},
        }},
    })

    resp = await sw.stripe_webhook(_FakeRequest())
    assert resp.get("received") is True

    ev = _events()[0]
    assert ev["status"] == "done"
    assert ev["amount"] == 2900
    assert ev["currency"] == "usd"

    buyers = _buyers()
    assert len(buyers) == 1
    assert buyers[0]["paid_amount"] == 2900
    assert buyers[0]["paid_currency"] == "usd"


async def test_non_revenue_event_records_null_amount(monkeypatch):
    _patch_event(monkeypatch, {
        "id": "evt_sub_created",
        "type": "customer.subscription.created",
        "data": {"object": {"id": "sub_none", "current_period_end": 0}},
    })

    resp = await sw.stripe_webhook(_FakeRequest())
    assert resp.get("received") is True

    ev = _events()[0]
    assert ev["status"] == "done"
    assert ev["amount"] is None
    assert ev["currency"] is None
