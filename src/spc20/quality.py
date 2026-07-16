"""Sensor signal quality classification.

Quality states are determined from the raw mA signal level.
Bad values are never silently clamped — the raw mA is preserved alongside the flag.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class QualityState(str, Enum):
    """4-20 mA loop quality states in priority order (worst first)."""
    LOOP_LOW_FAULT = "LOOP_LOW_FAULT"          # < 3.6 mA — open circuit / dead transmitter
    UNDER_RANGE_WARNING = "UNDER_RANGE_WARNING" # 3.6–3.9 mA — below 4 mA live zero
    GOOD = "GOOD"                               # 3.9–20.5 mA — healthy signal
    OVER_RANGE_WARNING = "OVER_RANGE_WARNING"   # 20.5–21.0 mA — slightly above 20 mA full scale
    LOOP_HIGH_FAULT = "LOOP_HIGH_FAULT"         # > 21.0 mA — shorted loop or transmitter fault
    CONFIG_ERROR = "CONFIG_ERROR"               # impossible / missing channel config


# Thresholds — can be overridden per site if needed
LOOP_LOW_FAULT_MA: float = 3.6
UNDER_RANGE_WARNING_MA: float = 3.9
OVER_RANGE_WARNING_MA: float = 20.5
LOOP_HIGH_FAULT_MA: float = 21.0


def classify(ma: float) -> QualityState:
    """Return the quality state for a raw mA reading."""
    if ma < LOOP_LOW_FAULT_MA:
        return QualityState.LOOP_LOW_FAULT
    if ma < UNDER_RANGE_WARNING_MA:
        return QualityState.UNDER_RANGE_WARNING
    if ma <= OVER_RANGE_WARNING_MA:
        return QualityState.GOOD
    if ma <= LOOP_HIGH_FAULT_MA:
        return QualityState.OVER_RANGE_WARNING
    return QualityState.LOOP_HIGH_FAULT


def is_usable(state: QualityState) -> bool:
    """Return True when a quality state is good enough for heuristic decisions."""
    return state in (QualityState.GOOD, QualityState.UNDER_RANGE_WARNING, QualityState.OVER_RANGE_WARNING)


def is_faulted(state: QualityState) -> bool:
    """Return True when a quality state indicates a loop fault that prevents measurement."""
    return state in (QualityState.LOOP_LOW_FAULT, QualityState.LOOP_HIGH_FAULT, QualityState.CONFIG_ERROR)


@dataclass
class QualityResult:
    channel: str
    raw_ma: float
    state: QualityState

    @property
    def usable(self) -> bool:
        return is_usable(self.state)

    @property
    def faulted(self) -> bool:
        return is_faulted(self.state)
