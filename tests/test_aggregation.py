"""Tests for spc20.aggregation — 60-sample → 1-minute summary."""
import os
import time
import pytest

os.environ.setdefault("DEVICE_ID", "test-device")
os.environ.setdefault("DEVICE_TOKEN", "test-token")
os.environ.setdefault("SUPABASE_INGEST_URL", "http://localhost/test")

from spc20.aggregation import summarise
from spc20.config import DeviceConfig, SensorRange
from spc20.adapters.base import RawSample


def _cfg() -> DeviceConfig:
    return DeviceConfig(
        device_id="test",
        device_token="test-token",
        supabase_url="http://localhost/test",
        sensor_adapter="simulator",
        p1=SensorRange(min_eu=-15.0, max_eu=15.0),
        p2=SensorRange(min_eu=0.0, max_eu=100.0),
        p3=SensorRange(min_eu=0.0, max_eu=100.0),
        flow=SensorRange(min_eu=0.0, max_eu=500.0),
    )


def _sample(p1_ma=7.5, p2_ma=9.0, p3_ma=7.2, flow_ma=12.8, pump=True) -> RawSample:
    return RawSample(
        p1_ma=p1_ma,
        p2_ma=p2_ma,
        p3_ma=p3_ma,
        flow_ma=flow_ma,
        pump_running=pump,
        timestamp=time.time(),
    )


def _samples(n=60, **kwargs) -> list[RawSample]:
    return [_sample(**kwargs) for _ in range(n)]


# ── avg / min / max / stddev ──────────────────────────────────────────────────

def test_avg_correct():
    samples = _samples(60, flow_ma=12.0)
    result = summarise(samples, _cfg())
    # 12.0 mA on 0-500 GPM range: (12-4)/16 * 500 = 250 GPM
    assert result["flow_gpm_avg"] == pytest.approx(250.0, abs=0.1)


def test_min_max_correct():
    # Two distinct values
    samples = [_sample(flow_ma=8.0)] * 30 + [_sample(flow_ma=16.0)] * 30
    result = summarise(samples, _cfg())
    # 8 mA → (8-4)/16*500=125 GPM; 16 mA → (16-4)/16*500=375 GPM
    assert result["flow_gpm_min"] == pytest.approx(125.0, abs=0.1)
    assert result["flow_gpm_max"] == pytest.approx(375.0, abs=0.1)


def test_stddev_zero_for_constant():
    samples = _samples(60, flow_ma=12.0)
    result = summarise(samples, _cfg())
    assert result["flow_gpm_stddev"] == pytest.approx(0.0, abs=0.01)


def test_stddev_positive_for_varying():
    samples = [_sample(flow_ma=8.0)] * 30 + [_sample(flow_ma=16.0)] * 30
    result = summarise(samples, _cfg())
    assert result["flow_gpm_stddev"] > 0.0


# ── near_zero_count ───────────────────────────────────────────────────────────

def test_near_zero_count_all_zero():
    # flow_ma=4.05 → EU ≈ 1.6 GPM (< 5.0 threshold)
    samples = _samples(60, flow_ma=4.05)
    result = summarise(samples, _cfg())
    assert result["flow_near_zero_count"] == 60


def test_near_zero_count_none_zero():
    # flow_ma=8.0 → 125 GPM (>> 5 GPM threshold)
    samples = _samples(60, flow_ma=8.0)
    result = summarise(samples, _cfg())
    assert result["flow_near_zero_count"] == 0


def test_near_zero_count_partial():
    low = [_sample(flow_ma=4.05)] * 10  # near-zero
    high = [_sample(flow_ma=12.0)] * 50  # normal
    result = summarise(low + high, _cfg())
    assert result["flow_near_zero_count"] == 10


# ── pulsing detection via coefficient_of_variation ───────────────────────────

def test_cv_zero_for_constant():
    samples = _samples(60, flow_ma=12.0)
    result = summarise(samples, _cfg())
    assert result["flow_cv"] == pytest.approx(0.0, abs=0.01)


def test_cv_elevated_for_pulsing():
    # Alternating near-zero and high values → high CV
    samples = [_sample(flow_ma=4.05)] * 30 + [_sample(flow_ma=16.0)] * 30
    result = summarise(samples, _cfg())
    assert result["flow_cv"] > 0.5


# ── other fields ──────────────────────────────────────────────────────────────

def test_pump_running_majority_rule():
    pump_on = [_sample(pump=True)] * 40
    pump_off = [_sample(pump=False)] * 20
    result = summarise(pump_on + pump_off, _cfg())
    assert result["pump_running"] is True


def test_pump_running_minority_false():
    pump_on = [_sample(pump=True)] * 20
    pump_off = [_sample(pump=False)] * 40
    result = summarise(pump_on + pump_off, _cfg())
    assert result["pump_running"] is False


def test_filter_dp_is_p2_minus_p3():
    # P2 avg = 9.0 mA → 31.25 PSI; P3 avg = 7.0 mA → 18.75 PSI; DP ≈ 12.5 PSI
    samples = _samples(60, p2_ma=9.0, p3_ma=7.0)
    result = summarise(samples, _cfg())
    expected_dp = result["p2_filter_inlet_psi_avg"] - result["p3_filter_outlet_psi_avg"]
    assert result["filter_dp_psi_avg"] == pytest.approx(expected_dp, abs=0.05)


def test_quality_keys_present():
    result = summarise(_samples(60), _cfg())
    assert "p1" in result["quality"]
    assert "p2" in result["quality"]
    assert "p3" in result["quality"]
    assert "flow" in result["quality"]


def test_raw_ma_preserved():
    samples = _samples(60, p1_ma=7.5)
    result = summarise(samples, _cfg())
    assert result["raw_ma"]["p1_avg"] == pytest.approx(7.5, abs=0.01)
