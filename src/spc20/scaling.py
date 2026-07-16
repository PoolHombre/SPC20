"""4-20 mA scaling utilities.

Converts raw milliamp readings to engineering units using a linear
transfer function across the sensor's declared engineering range.
"""
from __future__ import annotations
from .config import SensorRange


def ma_to_eu(ma: float, r: SensorRange) -> float:
    """Scale a 4-20 mA signal to engineering units.

    Uses linear interpolation between (4 mA → min_eu) and (20 mA → max_eu).
    Out-of-range mA values are NOT clamped — callers must check quality first.
    """
    return r.min_eu + (ma - 4.0) / 16.0 * (r.max_eu - r.min_eu)


def eu_to_ma(eu: float, r: SensorRange) -> float:
    """Inverse of ma_to_eu — converts engineering units back to mA."""
    return 4.0 + (eu - r.min_eu) / (r.max_eu - r.min_eu) * 16.0
