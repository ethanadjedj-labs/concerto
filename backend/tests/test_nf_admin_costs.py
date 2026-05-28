"""
Tests for NF admin dashboard cost-calculation math.

Verified rates (2026-05-20 via GET /v1/plans):
  nf-compute-20:    $0.008/hr
  nf-compute-100-1: $0.025/hr
  nf-compute-200:   $0.067/hr
  Volume NVMe:      $0.15/GB/month
"""

from datetime import datetime, timezone

import pytest

from concerto.nf_admin_router import (
    _PLAN_HOURLY_RATES,
    _VOLUME_GB_MONTHLY_RATE,
    compute_service_cost_month,
    compute_service_cost_today,
    compute_volume_cost_month,
    compute_volume_cost_today,
)


# ── Rate table sanity ──────────────────────────────────────────────────────────

def test_plan_rates_match_verified_values():
    assert _PLAN_HOURLY_RATES["nf-compute-20"] == 0.008
    assert _PLAN_HOURLY_RATES["nf-compute-100-1"] == 0.025
    assert _PLAN_HOURLY_RATES["nf-compute-200"] == 0.067


def test_volume_rate_matches_verified_value():
    assert _VOLUME_GB_MONTHLY_RATE == 0.15


# ── Service cost math ──────────────────────────────────────────────────────────

def _now(year=2026, month=5, day=20, hour=10) -> datetime:
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


def test_one_hour_nf_compute_200():
    now = _now(hour=11)
    # Service started exactly 1 hour before now, within the same day/month
    created = "2026-05-20T10:00:00Z"
    cost = compute_service_cost_month("nf-compute-200", created, now)
    assert abs(cost - 0.067) < 1e-9


def test_one_hour_nf_compute_20():
    now = _now(hour=11)
    created = "2026-05-20T10:00:00Z"
    cost = compute_service_cost_month("nf-compute-20", created, now)
    assert abs(cost - 0.008) < 1e-9


def test_one_hour_nf_compute_100_1():
    now = _now(hour=11)
    created = "2026-05-20T10:00:00Z"
    cost = compute_service_cost_month("nf-compute-100-1", created, now)
    assert abs(cost - 0.025) < 1e-9


def test_service_created_before_month_clips_to_month_start():
    # Service created last month: cost should only count from month start
    now = _now(month=5, day=2, hour=0)  # 2026-05-02 00:00 UTC
    created = "2026-04-15T00:00:00Z"    # before this month
    # Only 1 day (86400s / 3600 = 24h) has elapsed since month start
    cost = compute_service_cost_month("nf-compute-200", created, now)
    expected = 0.067 * 24  # 24 hours at $0.067/hr
    assert abs(cost - expected) < 1e-4


def test_service_created_this_month_counts_from_creation():
    now = _now(month=5, day=20, hour=12)  # noon
    created = "2026-05-20T10:00:00Z"      # 2 hours ago
    cost = compute_service_cost_month("nf-compute-200", created, now)
    expected = 0.067 * 2
    assert abs(cost - expected) < 1e-9


def test_unknown_plan_returns_zero():
    now = _now()
    created = "2026-05-01T00:00:00Z"
    cost = compute_service_cost_month("nf-compute-BOGUS", created, now)
    assert cost == 0.0


def test_service_cost_today_clips_to_day_start():
    # Service created yesterday; today's cost should only count from midnight
    now = _now(hour=6)  # 06:00 today
    created = "2026-05-19T12:00:00Z"  # yesterday afternoon
    cost = compute_service_cost_today("nf-compute-200", created, now)
    expected = 0.067 * 6  # 6 hours since midnight
    assert abs(cost - expected) < 1e-9


# ── Volume cost math ───────────────────────────────────────────────────────────

def test_6gb_volume_full_month():
    # Full 31-day May; 6 GB volume full month = $0.15 * 6 = $0.90
    # We test at end of month (day 31 23:59...) via ratio
    now = datetime(2026, 5, 31, 23, 59, 59, tzinfo=timezone.utc)
    cost = compute_volume_cost_month(6144, now)
    # days_elapsed ≈ 30.999... / 31 days ≈ ~$0.8999
    assert abs(cost - 0.15 * 6 * (30 + 23 / 24 + 59 / 1440 + 59 / 86400) / 31) < 1e-4


def test_6gb_volume_10_days_in_30_day_month():
    # $0.15 * 6 * (10/30) = $0.30 — using 30-day month (June)
    now = datetime(2026, 6, 11, 0, 0, 0, tzinfo=timezone.utc)  # exactly 10 days into June
    cost = compute_volume_cost_month(6144, now)
    expected = 0.15 * 6 * (10 / 30)
    assert abs(cost - expected) < 1e-6


def test_volume_monthly_rate_formula():
    # 1 GB volume, 15 days into a 31-day month
    now = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)  # exactly 15 days in
    cost = compute_volume_cost_month(1024, now)
    expected = 0.15 * 1 * (15 / 31)
    assert abs(cost - expected) < 1e-6


def test_volume_cost_today_is_fraction_of_daily_rate():
    # 6 GB volume, 12 hours into a 31-day month day
    now = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    cost = compute_volume_cost_today(6144, now)
    # daily_rate = 0.15 * 6 / 31; half a day elapsed
    daily_rate = 0.15 * 6 / 31
    expected = daily_rate * (12 / 24)
    assert abs(cost - expected) < 1e-5  # tolerance for round(..., 6)


def test_volume_size_zero():
    now = _now()
    assert compute_volume_cost_month(0, now) == 0.0
    assert compute_volume_cost_today(0, now) == 0.0
