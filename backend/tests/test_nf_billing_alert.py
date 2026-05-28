"""Unit tests for nf_billing_alert — cost computation and alert-state idempotency."""
import time
from datetime import datetime, timezone

import pytest

from concerto.nf_billing_alert import (
    _parse_ts,
    _should_alert,
    compute_costs,
)


# ── _parse_ts ──────────────────────────────────────────────────────────────────

class TestParseTs:
    def test_iso8601_with_z(self):
        ts = _parse_ts("2026-05-01T00:00:00Z")
        expected = datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp()
        assert abs(ts - expected) < 1

    def test_iso8601_without_z(self):
        ts = _parse_ts("2026-05-01T00:00:00")
        expected = datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp()
        assert abs(ts - expected) < 1

    def test_numeric_string(self):
        assert _parse_ts("1000000") == 1_000_000.0

    def test_none_returns_zero(self):
        assert _parse_ts(None) == 0.0

    def test_empty_string_returns_zero(self):
        assert _parse_ts("") == 0.0

    def test_int(self):
        assert _parse_ts(12345) == 12345.0


# ── compute_costs ──────────────────────────────────────────────────────────────

class TestComputeCosts:
    def _now(self, year: int, month: int, day: int, hour: int = 0) -> float:
        return datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp()

    def test_empty_inputs(self):
        costs = compute_costs([], [], now_ts=time.time())
        assert costs["mtd_total_usd"] == 0.0
        assert costs["mtd_compute_usd"] == 0.0
        assert costs["mtd_volume_usd"] == 0.0
        assert costs["active_service_count"] == 0

    def test_service_nf_compute_200_24h(self):
        """1 nf-compute-200 service running exactly 24h = $1.608."""
        now_ts = self._now(2026, 5, 15, 12)
        # created 24 hours before now, within the same month
        created_ts = self._now(2026, 5, 14, 12)
        services = [{
            "name": "concerto-abc",
            "billing": {"deploymentPlan": "nf-compute-200"},
            "createdAt": datetime(2026, 5, 14, 12, tzinfo=timezone.utc).isoformat(),
        }]
        costs = compute_costs(services, [], now_ts=now_ts)
        # $0.067/hr × 24h = $1.608
        assert abs(costs["mtd_compute_usd"] - 1.608) < 0.001
        assert costs["mtd_volume_usd"] == 0.0
        assert abs(costs["mtd_total_usd"] - 1.608) < 0.001

    def test_volume_6gb_10days(self):
        """1 volume 6 GB stored for 10 days = $0.30 (using 30-day billing month)."""
        now_ts = self._now(2026, 5, 11)   # May 11 00:00 UTC
        volumes = [{
            "spec": {"storageSize": 6144},  # 6144 MB = 6 GB
            "createdAt": datetime(2026, 5, 1, tzinfo=timezone.utc).isoformat(),
        }]
        costs = compute_costs([], volumes, now_ts=now_ts)
        # $0.15/GB-month × 6 GB × (10 days / 30 days) = $0.30
        assert abs(costs["mtd_volume_usd"] - 0.30) < 0.001
        assert costs["mtd_compute_usd"] == 0.0

    def test_cumulative_service_and_volume(self):
        """Service + volume costs accumulate correctly."""
        now_ts = self._now(2026, 5, 15, 12)
        created_iso = datetime(2026, 5, 14, 12, tzinfo=timezone.utc).isoformat()

        services = [{
            "name": "svc",
            "billing": {"deploymentPlan": "nf-compute-200"},
            "createdAt": created_iso,
        }]
        volumes = [{
            "spec": {"storageSize": 6144},
            "createdAt": created_iso,
        }]

        costs = compute_costs(services, volumes, now_ts=now_ts)

        # Compute: 24h × $0.067 = $1.608
        assert abs(costs["mtd_compute_usd"] - 1.608) < 0.001

        # Volume: 24h × (6 GB × $0.15 / (30 × 24)) = 24 × 0.00125 = $0.030
        assert abs(costs["mtd_volume_usd"] - 0.030) < 0.001

        assert abs(costs["mtd_total_usd"] - 1.638) < 0.002

    def test_service_created_before_month_start_billed_from_month_start(self):
        """Service created last month: only billed from start of current month."""
        now_ts = self._now(2026, 5, 2)   # 1 day into May
        services = [{
            "name": "old-svc",
            "billing": {"deploymentPlan": "nf-compute-200"},
            # created in April — should only bill from May 1
            "createdAt": datetime(2026, 4, 1, tzinfo=timezone.utc).isoformat(),
        }]
        costs = compute_costs(services, [], now_ts=now_ts)
        # 1 day × 24h × $0.067 = $1.608
        assert abs(costs["mtd_compute_usd"] - 1.608) < 0.001

    def test_unknown_plan_contributes_zero_compute(self):
        """Services on an unknown plan contribute $0 (we don't overcount)."""
        now_ts = self._now(2026, 5, 15, 12)
        services = [{
            "name": "mystery-svc",
            "billing": {"deploymentPlan": "nf-compute-unknown-future-plan"},
            "createdAt": datetime(2026, 5, 14, 12, tzinfo=timezone.utc).isoformat(),
        }]
        costs = compute_costs(services, [], now_ts=now_ts)
        assert costs["mtd_compute_usd"] == 0.0

    def test_daily_rate_extrapolation(self):
        """Daily rate = MTD total / days elapsed."""
        now_ts = self._now(2026, 5, 5)  # 4 days into May
        services = [{
            "name": "svc",
            "billing": {"deploymentPlan": "nf-compute-200"},
            "createdAt": datetime(2026, 5, 1, tzinfo=timezone.utc).isoformat(),
        }]
        costs = compute_costs(services, [], now_ts=now_ts)
        # Compute: 4 days × 24h × $0.067 = $6.432
        # Daily rate: $6.432 / 4 = $1.608
        assert abs(costs["daily_rate_usd"] - 1.608) < 0.01

    def test_multiple_services(self):
        """Multiple services sum correctly."""
        now_ts = self._now(2026, 5, 15, 12)
        created = datetime(2026, 5, 14, 12, tzinfo=timezone.utc).isoformat()
        services = [
            {"name": "a", "billing": {"deploymentPlan": "nf-compute-200"}, "createdAt": created},
            {"name": "b", "billing": {"deploymentPlan": "nf-compute-200-8"}, "createdAt": created},
        ]
        costs = compute_costs(services, [], now_ts=now_ts)
        # (0.067 + 0.072) × 24 = $3.336
        assert abs(costs["mtd_compute_usd"] - 3.336) < 0.001
        assert costs["active_service_count"] == 2

    def test_service_breakdown_present(self):
        now_ts = self._now(2026, 5, 15, 12)
        services = [{
            "name": "test-svc",
            "billing": {"deploymentPlan": "nf-compute-200"},
            "createdAt": datetime(2026, 5, 14, 12, tzinfo=timezone.utc).isoformat(),
        }]
        costs = compute_costs(services, [], now_ts=now_ts)
        assert len(costs["service_breakdown"]) == 1
        entry = costs["service_breakdown"][0]
        assert entry["name"] == "test-svc"
        assert entry["plan"] == "nf-compute-200"
        assert abs(entry["cost_usd"] - 1.608) < 0.001


# ── _should_alert ──────────────────────────────────────────────────────────────

class TestShouldAlert:
    def test_fires_on_first_trigger(self):
        state: dict = {}
        assert _should_alert(state, "mtd", 150.0, 100.0) is True

    def test_no_alert_below_threshold(self):
        state: dict = {}
        assert _should_alert(state, "mtd", 99.99, 100.0) is False

    def test_no_alert_at_exact_threshold(self):
        """Threshold is exclusive: value must strictly exceed it."""
        state: dict = {}
        assert _should_alert(state, "mtd", 100.0, 100.0) is False

    def test_no_double_alert_same_value(self):
        """Same alert fired twice → only one notification."""
        state: dict = {}
        # First fire
        assert _should_alert(state, "mtd", 150.0, 100.0) is True
        state["mtd"] = {"value": 150.0, "ts": time.time()}

        # Second call with same value → must not re-alert
        assert _should_alert(state, "mtd", 150.0, 100.0) is False

    def test_no_alert_slightly_worse(self):
        """10% worse is not enough to re-alert (threshold is 25%)."""
        state: dict = {}
        assert _should_alert(state, "mtd", 150.0, 100.0) is True
        state["mtd"] = {"value": 150.0, "ts": time.time()}

        assert _should_alert(state, "mtd", 165.0, 100.0) is False

    def test_re_alert_when_25pct_worse(self):
        """25% worse → re-alert."""
        state: dict = {}
        assert _should_alert(state, "mtd", 150.0, 100.0) is True
        state["mtd"] = {"value": 150.0, "ts": time.time()}

        assert _should_alert(state, "mtd", 187.5, 100.0) is True

    def test_re_alert_after_clear(self):
        """Condition clears then re-triggers → alert fires again."""
        state: dict = {}
        # First alert
        assert _should_alert(state, "mtd", 150.0, 100.0) is True
        state["mtd"] = {"value": 150.0, "ts": time.time()}

        # Condition clears (value drops below threshold)
        assert _should_alert(state, "mtd", 80.0, 100.0) is False
        state.pop("mtd", None)  # caller clears state when condition inactive

        # Condition re-triggers
        assert _should_alert(state, "mtd", 105.0, 100.0) is True

    def test_independent_keys_do_not_interfere(self):
        """State for 'mtd' and 'rate' are independent."""
        state: dict = {}
        state["mtd"] = {"value": 150.0, "ts": time.time()}

        # rate key has no prior state → should alert
        assert _should_alert(state, "rate", 60.0, 50.0) is True
        # mtd key has state → should not re-alert at same value
        assert _should_alert(state, "mtd", 150.0, 100.0) is False
