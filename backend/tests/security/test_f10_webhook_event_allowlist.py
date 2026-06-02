"""F-10 — Stripe webhook must allow-list the event types it dispatches.

Old behaviour: any signed event type (e.g. `customer.updated`,
`invoice.created`, `product.deleted`) was claimed in
`stripe_processed_events` and returned `{"received": True}` even though
no handler ever touches the row.  That:

  * grows the dedupe table unboundedly with events the system does not act on,
  * masks a future regression where a new handler is added but the
    event-type spelling is wrong (the call appears to "succeed"
    because the catch-all 200 path is taken).

The hardened contract:

  * `_dispatch_event` returns a sentinel `{"ignored": True, "reason":
    "unhandled event type"}` for unknown types,
  * the endpoint returns 200 BUT does NOT write to
    `stripe_processed_events` for unknown types,
  * the set of allowed types is centralised so a code-grep audit can
    enumerate exactly what the system acts on.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest

# ── Scratch DB wiring — MUST precede any concerto import ──────────────────────
_SCRATCH_DIR = tempfile.mkdtemp(prefix="concerto-f10-")
_SCRATCH_DB = os.path.join(_SCRATCH_DIR, "scratch.db")
os.environ["CONCERTO_DB_PATH"] = _SCRATCH_DB
os.environ.setdefault("STRIPE_CONCERTO_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")

from concerto import db  # noqa: E402
from concerto import stripe_webhook as sw  # noqa: E402


_MIGRATIONS = [
    "001_init.sql", "002_ttyd_credentials.sql", "003_hosted_plan.sql",
    "004_operator_kit.sql", "005_stripe_customer_id.sql",
    "006_drip_tracking.sql", "007_recovery.sql", "007_pricing_tiers_v2.sql",
    "008_rename_maestro_to_concerto.sql", "009_trial_mode.sql",
    "010_email_dead_letter.sql", "012_plan_check_solo_pro.sql",
    "013_cf_tunnel_tracking.sql", "014_stripe_customer_id_index.sql",
    "015_github_token.sql", "016_pre_expiry_warned_at.sql",
    "017_auto_pause.sql", "018_callback_secret.sql",
    "019_github_concerto_repo.sql", "020_lifecycle_events.sql",
    "021_github_login.sql", "022_stripe_event_amounts.sql",
]


def _apply_migrations() -> None:
    mig_dir = os.path.join(os.path.dirname(__file__), "..", "..", "migrations")
    conn = sqlite3.connect(_SCRATCH_DB)
    try:
        for fname in _MIGRATIONS:
            with open(os.path.join(mig_dir, fname)) as f:
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
    monkeypatch.setattr(db, "DB_PATH", _SCRATCH_DB)
    monkeypatch.setattr(sw, "_WEBHOOK_SECRET", "whsec_test")
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(_SCRATCH_DB + suffix)
        except FileNotFoundError:
            pass
    _apply_migrations()
    yield


def _events() -> list[dict]:
    conn = sqlite3.connect(_SCRATCH_DB)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM stripe_processed_events"
        ).fetchall()]
    finally:
        conn.close()


class _FakeRequest:
    headers = {"stripe-signature": "sig_test"}

    async def body(self) -> bytes:
        return b"{}"


def _patch_event(monkeypatch, event: dict) -> None:
    monkeypatch.setattr(sw.stripe.Webhook, "construct_event", lambda *a, **k: event)


async def test_f10_unknown_event_type_does_not_persist(monkeypatch):
    """An unhandled but signed event type must not bloat the dedupe table."""
    _patch_event(monkeypatch, {
        "id": "evt_unknown_1",
        "type": "customer.updated",  # never dispatched by Concerto
        "data": {"object": {"id": "cus_test", "metadata": {}}},
    })

    resp = await sw.stripe_webhook(_FakeRequest())
    assert resp.get("ignored") is True
    assert "unhandled" in (resp.get("reason") or "").lower()

    # The key contract: no row inserted, no resources consumed.
    assert _events() == [], (
        "F-10: unknown event types must NOT be recorded in "
        "stripe_processed_events (this row grows unboundedly)"
    )


async def test_f10_known_event_type_still_processed(monkeypatch):
    """Sanity: real handled types still run end-to-end after the allow-list."""
    async def _noop_email(*_a, **_k):
        return None

    monkeypatch.setattr(sw, "send_email", _noop_email)
    monkeypatch.setattr("concerto.drip_runner.send_immediate_drip", lambda *_a, **_k: None)

    _patch_event(monkeypatch, {
        "id": "evt_known_1",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test", "amount_total": 2900, "currency": "usd",
            "customer": "cus_123",
            "metadata": {"product": "concerto", "plan": "solo"},
        }},
    })

    resp = await sw.stripe_webhook(_FakeRequest())
    assert resp.get("received") is True

    rows = _events()
    assert len(rows) == 1
    assert rows[0]["status"] == "done"


def test_f10_allowlist_is_exhaustive_with_dispatcher():
    """The allow-list must include every event type the dispatcher handles.

    If a new `elif event_type == "..."` is added without updating the
    allow-list, this test fails — preventing a regression where the
    handler exists but the gate drops the event before it reaches the
    handler.
    """
    import inspect, re

    src = inspect.getsource(sw._dispatch_event)
    handled = set(re.findall(r'event_type == "([^"]+)"', src))
    allowed = set(getattr(sw, "_ALLOWED_EVENT_TYPES", set()))

    missing = handled - allowed
    assert not missing, (
        f"F-10: _dispatch_event handles event types not in "
        f"_ALLOWED_EVENT_TYPES: {sorted(missing)}"
    )
