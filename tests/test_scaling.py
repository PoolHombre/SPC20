import pytest
from src.config import SensorRange
from src.sensors import ma_to_eu, quality


def test_p1_min():
    r = SensorRange(min_eu=-15.0, max_eu=15.0)
    assert ma_to_eu(4.0, r) == pytest.approx(-15.0)


def test_p1_max():
    r = SensorRange(min_eu=-15.0, max_eu=15.0)
    assert ma_to_eu(20.0, r) == pytest.approx(15.0)


def test_p1_midpoint():
    r = SensorRange(min_eu=-15.0, max_eu=15.0)
    assert ma_to_eu(12.0, r) == pytest.approx(0.0)


def test_p2_min():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    assert ma_to_eu(4.0, r) == pytest.approx(0.0)


def test_p2_max():
    r = SensorRange(min_eu=0.0, max_eu=100.0)
    assert ma_to_eu(20.0, r) == pytest.approx(100.0)


def test_flow_midpoint():
    r = SensorRange(min_eu=0.0, max_eu=500.0)
    assert ma_to_eu(12.0, r) == pytest.approx(250.0)


def test_quality_good():
    assert quality(12.0) == "GOOD"


def test_quality_under():
    assert quality(3.5) == "FAULT_UNDER"


def test_quality_over():
    assert quality(21.0) == "FAULT_OVER"
