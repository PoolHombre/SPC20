"""Tests for spc20.heuristics — dispatch rule evaluation."""
import os
import pytest

os.environ.setdefault("DEVICE_ID", "test-device")
os.environ.setdefault("DEVICE_TOKEN", "test-token")
os.environ.setdefault("SUPABASE_INGEST_URL", "http://localhost/test")

from spc20.heuristics import evaluate
from spc20.config import DeviceConfig


def _cfg() -> DeviceConfig:
    return DeviceConfig(
        device_id="test",
        device_token="test-token",
        supabase_url="http://localhost/test",
        sensor_adapter="simulator",
        required_flow_gpm=300.0,
        normal_flow_gpm_min=280.0,
        filter_clean_dp_psi=5.0,
        filter_service_dp_psi=12.0,
        filter_dp_hard_limit_psi=18.0,
        p2_max_psi=80.0,
        low_flow_red_threshold_percent=20.0,   # RED threshold = 60 GPM
        calibration_p23_tolerance_psi=0.5,
    )


def _base(**overrides) -> dict:
    """Return a valid GREEN summary dict with optional overrides."""
    b = {
        "pump_running": True,
        "flow_gpm_avg": 320.0,
        "flow_gpm_min": 310.0,
        "flow_gpm_max": 335.0,
        "flow_gpm_stddev": 3.0,
        "flow_cv": 0.009,
        "flow_near_zero_count": 0,
        "p1_suction_psi_avg": -3.5,
        "p2_filter_inlet_psi_avg": 28.0,
        "p3_filter_outlet_psi_avg": 20.0,
        "filter_dp_psi_avg": 6.0,
        "quality": {
            "p1": "GOOD",
            "p2": "GOOD",
            "p3": "GOOD",
            "flow": "GOOD",
        },
    }
    b.update(overrides)
    return b


CFG = _cfg()


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_green_normal():
    r = evaluate(_base(), CFG)
    assert r.dispatch_status == "GREEN"
    assert r.dispatch_action == "NO_VISIT"
    assert r.reason == "ALL_NORMAL"
    assert r.confidence == 1.0


def test_green_has_no_checks():
    r = evaluate(_base(), CFG)
    assert r.recommended_first_checks == []


def test_green_pump_off_no_faults():
    """Pump off with no fault quality — should be GREEN (no RED rules fire)."""
    r = evaluate(_base(pump_running=False, flow_gpm_avg=0.0, flow_gpm_stddev=0.0), CFG)
    assert r.dispatch_status == "GREEN"


# ── RED: LOW_WATER_LOSING_PRIME ───────────────────────────────────────────────

def test_red_low_water_pulsing_high_stddev():
    r = evaluate(_base(
        flow_gpm_avg=30.0,
        flow_gpm_stddev=25.0,  # high stddev → pulsing
        flow_cv=0.5,
        near_zero_count=0,
    ), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "LOW_WATER_LOSING_PRIME"


def test_red_low_water_pulsing_high_cv():
    r = evaluate(_base(
        flow_gpm_avg=30.0,
        flow_gpm_stddev=5.0,
        flow_cv=0.4,  # > 0.3 threshold
        flow_near_zero_count=0,
    ), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "LOW_WATER_LOSING_PRIME"


def test_red_low_water_pulsing_near_zero_count():
    r = evaluate(_base(
        flow_gpm_avg=30.0,
        flow_gpm_stddev=2.0,
        flow_cv=0.05,
        flow_near_zero_count=10,  # > 5 threshold
    ), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "LOW_WATER_LOSING_PRIME"


def test_low_water_checks_include_water_level():
    r = evaluate(_base(
        flow_gpm_avg=30.0,
        flow_gpm_stddev=25.0,
        flow_cv=0.5,
    ), CFG)
    checks_text = " ".join(r.recommended_first_checks).lower()
    assert "water" in checks_text or "level" in checks_text or "skimmer" in checks_text


# ── RED: NO_FLOW_PUMP_ON ──────────────────────────────────────────────────────

def test_red_no_flow_pump_on():
    r = evaluate(_base(
        flow_gpm_avg=5.0,
        flow_gpm_stddev=0.5,   # low stddev — not pulsing
        flow_cv=0.05,
        flow_near_zero_count=0,
    ), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "NO_FLOW_PUMP_ON"


# ── RED: HIGH_PRESSURE_OR_BLOCKED_FILTER ─────────────────────────────────────

def test_red_high_p2_pressure():
    r = evaluate(_base(p2_filter_inlet_psi_avg=85.0), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "HIGH_PRESSURE_OR_BLOCKED_FILTER"


def test_red_high_filter_dp():
    r = evaluate(_base(filter_dp_psi_avg=20.0), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "HIGH_PRESSURE_OR_BLOCKED_FILTER"


# ── RED: INVALID_PRESSURE_RELATIONSHIP ───────────────────────────────────────

def test_red_invalid_p3_gte_p2_pump_on():
    r = evaluate(_base(
        p2_filter_inlet_psi_avg=20.0,
        p3_filter_outlet_psi_avg=25.0,  # P3 > P2
        pump_running=True,
    ), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "INVALID_PRESSURE_RELATIONSHIP"


def test_pump_off_p3_gte_p2_does_not_fire():
    """INVALID_PRESSURE_RELATIONSHIP must NOT fire when pump is off."""
    r = evaluate(_base(
        pump_running=False,
        flow_gpm_avg=0.0,
        flow_gpm_stddev=0.0,
        p2_filter_inlet_psi_avg=20.0,
        p3_filter_outlet_psi_avg=25.0,  # P3 > P2 — but pump is off
    ), CFG)
    assert r.reason != "INVALID_PRESSURE_RELATIONSHIP"


# ── RED: SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION ──────────────────────────────

def test_red_sensor_fault_loop_low():
    r = evaluate(_base(quality={
        "p1": "LOOP_LOW_FAULT",
        "p2": "GOOD",
        "p3": "GOOD",
        "flow": "GOOD",
    }), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION"


def test_red_sensor_fault_loop_high():
    r = evaluate(_base(quality={
        "p1": "GOOD",
        "p2": "LOOP_HIGH_FAULT",
        "p3": "GOOD",
        "flow": "GOOD",
    }), CFG)
    assert r.dispatch_status == "RED"
    assert r.reason == "SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION"


def test_sensor_fault_pump_off_does_not_fire():
    """Loop fault when pump is OFF should not trigger RED (can't verify circulation either way but risk is lower)."""
    r = evaluate(_base(
        pump_running=False,
        flow_gpm_avg=0.0,
        flow_gpm_stddev=0.0,
        quality={"p1": "LOOP_LOW_FAULT", "p2": "GOOD", "p3": "GOOD", "flow": "GOOD"},
    ), CFG)
    # Pump is off — sensor fault RED should not fire
    assert r.reason != "SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION"


# ── YELLOW: FILTER_SERVICE_SOON ──────────────────────────────────────────────

def test_yellow_filter_service_at_threshold():
    r = evaluate(_base(filter_dp_psi_avg=12.0), CFG)  # exactly at threshold
    assert r.dispatch_status == "YELLOW"
    assert r.reason == "FILTER_SERVICE_SOON"


def test_yellow_filter_service_above_threshold():
    r = evaluate(_base(filter_dp_psi_avg=14.0), CFG)
    assert r.dispatch_status == "YELLOW"
    assert r.reason == "FILTER_SERVICE_SOON"


# ── YELLOW: FLOW_DECLINING ────────────────────────────────────────────────────

def test_yellow_flow_declining():
    r = evaluate(_base(flow_gpm_avg=260.0, flow_gpm_stddev=2.0, filter_dp_psi_avg=4.0), CFG)
    assert r.dispatch_status == "YELLOW"
    assert r.reason == "FLOW_DECLINING"


# ── Startup transient handling ────────────────────────────────────────────────

def test_missing_quality_keys_do_not_crash():
    """Evaluate should not raise even if quality dict is empty."""
    summary = _base()
    summary["quality"] = {}
    r = evaluate(summary, CFG)
    # With no quality data the heuristic should still return a result (not crash)
    assert r.dispatch_status in ("GREEN", "YELLOW", "RED")


def test_zero_flow_pump_off_is_green():
    """Pump off with zero flow is the normal idle state — should be GREEN."""
    r = evaluate(_base(
        pump_running=False,
        flow_gpm_avg=0.0,
        flow_gpm_min=0.0,
        flow_gpm_max=0.0,
        flow_gpm_stddev=0.0,
        flow_cv=0.0,
        flow_near_zero_count=60,
        filter_dp_psi_avg=5.0,
    ), CFG)
    assert r.dispatch_status == "GREEN"


# ── Legacy property aliases ───────────────────────────────────────────────────

def test_legacy_status_alias():
    r = evaluate(_base(), CFG)
    assert r.status == r.dispatch_status


def test_legacy_action_alias():
    r = evaluate(_base(), CFG)
    assert r.action == r.dispatch_action
