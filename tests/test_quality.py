"""Tests for spc20.quality — signal quality classification."""
import pytest
from spc20.quality import QualityState, classify, is_usable, is_faulted, QualityResult


# ── classify() — all 5 non-error states ──────────────────────────────────────

def test_loop_low_fault():
    assert classify(2.0) == QualityState.LOOP_LOW_FAULT


def test_under_range_warning():
    assert classify(3.7) == QualityState.UNDER_RANGE_WARNING


def test_good():
    assert classify(12.0) == QualityState.GOOD


def test_over_range_warning():
    assert classify(20.7) == QualityState.OVER_RANGE_WARNING


def test_loop_high_fault():
    assert classify(22.0) == QualityState.LOOP_HIGH_FAULT


# ── Boundary values ───────────────────────────────────────────────────────────

def test_exactly_3_6_is_loop_low_fault():
    # 3.6 mA is the exact lower boundary — < 3.6 is LOW_FAULT, 3.6 itself is UNDER_RANGE
    # classify uses `if ma < LOOP_LOW_FAULT_MA` so 3.6 is NOT low fault
    assert classify(3.6) == QualityState.UNDER_RANGE_WARNING


def test_just_below_3_6_is_loop_low_fault():
    assert classify(3.59) == QualityState.LOOP_LOW_FAULT


def test_exactly_3_9_is_good():
    # classify: if ma < 3.9 → UNDER_RANGE, if ma <= 20.5 → GOOD
    # 3.9 is NOT < 3.9, so it becomes GOOD
    assert classify(3.9) == QualityState.GOOD


def test_just_below_3_9_is_under_range():
    assert classify(3.89) == QualityState.UNDER_RANGE_WARNING


def test_exactly_20_5_is_good():
    # classify: if ma <= 20.5 → GOOD
    assert classify(20.5) == QualityState.GOOD


def test_just_above_20_5_is_over_range():
    assert classify(20.51) == QualityState.OVER_RANGE_WARNING


def test_exactly_21_0_is_over_range():
    # classify: if ma <= 21.0 → OVER_RANGE_WARNING
    assert classify(21.0) == QualityState.OVER_RANGE_WARNING


def test_just_above_21_0_is_high_fault():
    assert classify(21.01) == QualityState.LOOP_HIGH_FAULT


# ── is_usable() ───────────────────────────────────────────────────────────────

def test_good_is_usable():
    assert is_usable(QualityState.GOOD) is True


def test_under_range_warning_is_usable():
    assert is_usable(QualityState.UNDER_RANGE_WARNING) is True


def test_over_range_warning_is_usable():
    assert is_usable(QualityState.OVER_RANGE_WARNING) is True


def test_loop_low_fault_not_usable():
    assert is_usable(QualityState.LOOP_LOW_FAULT) is False


def test_loop_high_fault_not_usable():
    assert is_usable(QualityState.LOOP_HIGH_FAULT) is False


def test_config_error_not_usable():
    assert is_usable(QualityState.CONFIG_ERROR) is False


# ── is_faulted() ─────────────────────────────────────────────────────────────

def test_loop_low_fault_is_faulted():
    assert is_faulted(QualityState.LOOP_LOW_FAULT) is True


def test_loop_high_fault_is_faulted():
    assert is_faulted(QualityState.LOOP_HIGH_FAULT) is True


def test_config_error_is_faulted():
    assert is_faulted(QualityState.CONFIG_ERROR) is True


def test_good_not_faulted():
    assert is_faulted(QualityState.GOOD) is False


def test_under_range_not_faulted():
    assert is_faulted(QualityState.UNDER_RANGE_WARNING) is False


def test_over_range_not_faulted():
    assert is_faulted(QualityState.OVER_RANGE_WARNING) is False


# ── QualityResult dataclass ───────────────────────────────────────────────────

def test_quality_result_usable_property():
    qr = QualityResult(channel="p1", raw_ma=12.0, state=QualityState.GOOD)
    assert qr.usable is True
    assert qr.faulted is False


def test_quality_result_faulted_property():
    qr = QualityResult(channel="p1", raw_ma=2.0, state=QualityState.LOOP_LOW_FAULT)
    assert qr.usable is False
    assert qr.faulted is True
