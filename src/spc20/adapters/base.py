"""Abstract base class for sensor adapters."""
from __future__ import annotations
import abc
from dataclasses import dataclass


@dataclass
class RawSample:
    """One instantaneous set of raw sensor readings."""
    p1_ma: float       # P1 suction pressure (mA)
    p2_ma: float       # P2 filter inlet pressure (mA)
    p3_ma: float       # P3 filter outlet pressure (mA)
    flow_ma: float     # Flow (mA)
    pump_running: bool # Digital pump-run signal
    timestamp: float   # Unix epoch (seconds)


class SensorAdapter(abc.ABC):
    """Protocol for reading one set of raw sensor samples."""

    @abc.abstractmethod
    def read(self) -> RawSample:
        """Return a single instantaneous raw sample."""
        ...
