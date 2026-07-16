import pytest
from src.config import DeviceConfig
from src.heuristics import evaluate


def _base(overrides: dict) -> dict:
    base = {
        "pump_running": True,
        "flow_gpm_avg": 340.0,
        "flow_gpm_min": 330.0,
        "flow_gpm_max": 355.0,
        "flow_gpm_stddev": 4.0,
        "p1_suction_psi_avg": -3.5,
        "p2_filter_inlet_psi_avg": 30.0,
        "p3_filter_outlet_psi_avg": 22.0,
        "filter_dp_psi_avg": 8.0,
        "quality": {"p1": "GOOD", "p2": "GOOD", "p3": "GOOD", "flow": "GOOD"},
    }
    base.update(overrides)
    return base


CFG = DeviceConfig(
    device_id="test",
    device_token="test",
    supabase_url="http://localhost",
    sensor_adapter="simulator",
)


def test_green_normal():
    r = evaluate(_base({}), CFG)
    assert r.status == "GREEN"
    assert r.action == "NO_VISIT"


def test_red_no_flow():
    r = evaluate(_base({"flow_gpm_avg": 5.0, "flow_gpm_stddev": 1.0}), CFG)
    assert r.status == "RED"
    assert "NO_FLOW" in r.reason or "PRIME" in r.reason


def test_red_loss_of_prime():
    r = evaluate(_base({"flow_gpm_avg": 20.0, "flow_gpm_stddev": 35.0}), CFG)
    assert r.status == "RED"
    assert "PRIME" in r.reason


def test_red_sensor_fault():
    r = evaluate(_base({"quality": {"p1": "FAULT_UNDER", "p2": "GOOD", "p3": "GOOD", "flow": "GOOD"}}), CFG)
    assert r.status == "RED"
    assert "SENSOR" in r.reason


def test_red_invalid_pressure():
    r = evaluate(_base({"p2_filter_inlet_psi_avg": 20.0, "p3_filter_outlet_psi_avg": 25.0}), CFG)
    assert r.status == "RED"
    assert "PRESSURE" in r.reason


def test_yellow_filter_service():
    r = evaluate(_base({"filter_dp_psi_avg": 13.0}), CFG)
    assert r.status == "YELLOW"
    assert "FILTER" in r.reason


def test_yellow_flow_low():
    r = evaluate(_base({"flow_gpm_avg": 260.0, "flow_gpm_stddev": 3.0}), CFG)
    assert r.status == "YELLOW"
    assert "FLOW" in r.reason
