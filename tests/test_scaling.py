"""Tests for 4-20 mA scaling (spc20.scaling)."""
import pytest
from spc20.scaling import ma_to_eu, eu_to_ma
from spc20.config import SensorRange


# ── Standard range (0-100 PSI) ───────────────────────────────────────────────

def test_4ma_maps_to_min():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    assert ma_to_eu(4.0, r) == pytest.approx(0.0)


def test_12ma_maps_to_midpoint():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    assert ma_to_eu(12.0, r) == pytest.approx(50.0)


def test_20ma_maps_to_max():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    assert ma_to_eu(20.0, r) == pytest.approx(100.0)


# ── P1 vacuum / compound range (-15 to +15 PSI) ──────────────────────────────

def test_p1_4ma_is_minus15():
    r = SensorRange(min_eu=-15.0, max_eu=15.0)
    assert ma_to_eu(4.0, r) == pytest.approx(-15.0)


def test_p1_12ma_is_zero():
    r = SensorRange(min_eu=-15.0, max_eu=15.0)
    assert ma_to_eu(12.0, r) == pytest.approx(0.0)


def test_p1_20ma_is_plus15():
    r = SensorRange(min_eu=-15.0, max_eu=15.0)
    assert ma_to_eu(20.0, r) == pytest.approx(15.0)


# ── Configurable range (flow 0-500 GPM) ──────────────────────────────────────

def test_flow_midpoint():
    r = SensorRange(min_eu=0.0, max_eu=500.0)
    assert ma_to_eu(12.0, r) == pytest.approx(250.0)


def test_flow_4ma_is_zero():
    r = SensorRange(min_eu=0.0, max_eu=500.0)
    assert ma_to_eu(4.0, r) == pytest.approx(0.0)


def test_flow_20ma_is_max():
    r = SensorRange(min_eu=0.0, max_eu=500.0)
    assert ma_to_eu(20.0, r) == pytest.approx(500.0)


# ── Inverse function ──────────────────────────────────────────────────────────

def test_eu_to_ma_round_trip():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    for ma in [4.0, 8.0, 12.0, 16.0, 20.0]:
        eu = ma_to_eu(ma, r)
        assert eu_to_ma(eu, r) == pytest.approx(ma)


# ── Out-of-range values (not clamped — caller must check quality first) ───────

def test_overrange_not_clamped():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    # 22 mA should give > 100 EU (not clamped)
    assert ma_to_eu(22.0, r) > 100.0


def test_underrange_not_clamped():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    # 2 mA should give < 0 EU (not clamped)
    assert ma_to_eu(2.0, r) < 0.0
