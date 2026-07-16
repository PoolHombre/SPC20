"""Tests for spc20.calibration — ambient_zero and static_baseline modes."""
import os
import tempfile
import pytest

os.environ.setdefault("DEVICE_ID", "test-device")
os.environ.setdefault("DEVICE_TOKEN", "test-token")
os.environ.setdefault("SUPABASE_INGEST_URL", "http://localhost/test")

from spc20.calibration import Calibrator
from spc20.config import DeviceConfig, SensorRange


def _cfg(db_path: str) -> DeviceConfig:
    return DeviceConfig(
        device_id="test",
        device_token="test-token",
        supabase_url="http://localhost/test",
        sensor_adapter="simulator",
        calibration_sample_seconds=1,   # very short for tests
        sample_interval_sec=0.01,        # fast sampling
        calibration_stddev_limit=0.05,
        db_path=db_path,
    )


@pytest.fixture()
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name


# ── ambient_zero ──────────────────────────────────────────────────────────────

def test_ambient_zero_accepted_stable(db_path):
    """Stable signal near 4.0 mA → accepted with offset ≈ -4.0."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    # Stable 4.0 mA read (no noise)
    result = cal.ambient_zero(lambda: 4.0, channel="p1")
    assert result.accepted is True
    assert result.offset_value == pytest.approx(-4.0, abs=0.01)
    assert result.channel == "p1"
    assert result.mode == "ambient_zero"
    assert result.stddev == pytest.approx(0.0, abs=0.001)


def test_ambient_zero_offset_calculation(db_path):
    """Offset is negative mean — adding offset to future reading zeroes it out."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    result = cal.ambient_zero(lambda: 4.5, channel="p2")
    assert result.accepted is True
    # Offset = -4.5 so that 4.5 + (-4.5) = 0 (the true zero reading)
    assert result.offset_value == pytest.approx(-4.5, abs=0.01)


def test_ambient_zero_rejected_unstable(db_path):
    """High stddev signal → rejected, no offset stored."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    # Alternate between 4.0 and 4.5 to create high stddev
    values = [4.0, 4.5] * 50
    it = iter(values)
    result = cal.ambient_zero(lambda: next(it), channel="p3")
    assert result.accepted is False
    assert result.offset_value is None
    assert result.rejection_reason is not None
    assert "stddev" in result.rejection_reason.lower() or "Stddev" in result.rejection_reason


def test_ambient_zero_stores_event(db_path):
    """Accepted calibration event is persisted to DB."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    cal.ambient_zero(lambda: 4.0, channel="p1")
    offsets = cal.get_active_offsets()
    assert "p1" in offsets
    assert offsets["p1"] == pytest.approx(-4.0, abs=0.01)


# ── static_baseline ───────────────────────────────────────────────────────────

def test_static_baseline_pump_off(db_path):
    """Static baseline accepted when pump_running=False."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    result = cal.static_baseline(
        read_p2_ma=lambda: 8.0,
        read_p3_ma=lambda: 7.5,
        pump_running=False,
    )
    assert result.accepted is True
    assert result.p2_static_mean == pytest.approx(8.0, abs=0.01)
    assert result.p3_static_mean == pytest.approx(7.5, abs=0.01)
    assert result.static_p23_offset == pytest.approx(0.5, abs=0.01)  # p2 - p3


def test_static_baseline_raises_if_pump_on(db_path):
    """Static baseline must raise ValueError if pump_running=True."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    with pytest.raises(ValueError, match="pump_running"):
        cal.static_baseline(
            read_p2_ma=lambda: 8.0,
            read_p3_ma=lambda: 7.5,
            pump_running=True,
        )


def test_static_baseline_zero_when_equal(db_path):
    """If P2 == P3, static_p23_offset should be 0."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    result = cal.static_baseline(
        read_p2_ma=lambda: 7.0,
        read_p3_ma=lambda: 7.0,
        pump_running=False,
    )
    assert result.static_p23_offset == pytest.approx(0.0, abs=0.01)


# ── get_active_offsets ────────────────────────────────────────────────────────

def test_get_active_offsets_empty(db_path):
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    offsets = cal.get_active_offsets()
    assert offsets == {}


def test_get_active_offsets_most_recent_wins(db_path):
    """Second calibration for same channel supersedes the first."""
    cfg = _cfg(db_path)
    cal = Calibrator(cfg)
    cal.ambient_zero(lambda: 4.0, channel="p1")
    cal.ambient_zero(lambda: 4.2, channel="p1")
    offsets = cal.get_active_offsets()
    # Most recent: offset = -4.2
    assert offsets["p1"] == pytest.approx(-4.2, abs=0.02)
