from __future__ import annotations
import abc
import math
import random
import time
from dataclasses import dataclass
from typing import Protocol

from .config import DeviceConfig, SensorRange


UNDER_RANGE_MA = 3.8
OVER_RANGE_MA = 20.5


@dataclass
class RawSample:
    p1_ma: float
    p2_ma: float
    p3_ma: float
    flow_ma: float
    pump_running: bool
    timestamp: float


def ma_to_eu(ma: float, r: SensorRange) -> float:
    """Scale 4-20 mA to engineering units."""
    return r.min_eu + (ma - 4.0) / 16.0 * (r.max_eu - r.min_eu)


def quality(ma: float) -> str:
    if ma < UNDER_RANGE_MA:
        return "FAULT_UNDER"
    if ma > OVER_RANGE_MA:
        return "FAULT_OVER"
    return "GOOD"


class SensorAdapter(abc.ABC):
    @abc.abstractmethod
    def read(self) -> RawSample:
        ...


class SequentAdapter(SensorAdapter):
    """Real Sequent Microsystems Industrial HAT reader."""

    def __init__(self) -> None:
        try:
            import smbus2  # type: ignore
            self._bus = smbus2.SMBus(1)
        except ImportError:
            raise RuntimeError("smbus2 not installed — run: pip install smbus2")

    def read(self) -> RawSample:
        # Sequent Microsystems 4-20mA HAT register map (adjust to match your HAT revision)
        # Channels return raw 16-bit value; divide by 1000 to get mA
        def _read_channel(ch: int) -> float:
            addr = 0x40 + ch
            raw = self._bus.read_word_data(addr, 0x00)
            return raw / 1000.0

        # Digital input 1 on Sequent HAT — adjust address/register as needed
        pump = bool(self._bus.read_byte_data(0x20, 0x00) & 0x01)

        return RawSample(
            p1_ma=_read_channel(0),
            p2_ma=_read_channel(1),
            p3_ma=_read_channel(2),
            flow_ma=_read_channel(3),
            pump_running=pump,
            timestamp=time.time(),
        )


class SimulatorAdapter(SensorAdapter):
    """Generates synthetic 4-20 mA samples. Scenario driven by env or argument."""

    SCENARIOS = [
        "green",
        "yellow_filter",
        "red_loss_of_prime",
        "red_no_flow",
        "red_stale",
        "fault_under",
        "fault_over",
        "invalid_p3_p2",
    ]

    def __init__(self, scenario: str = "green") -> None:
        self.scenario = scenario
        self._t = 0

    def read(self) -> RawSample:
        self._t += 1
        s = self.scenario

        if s == "green":
            return RawSample(
                p1_ma=7.5 + random.gauss(0, 0.05),
                p2_ma=9.0 + random.gauss(0, 0.05),
                p3_ma=7.2 + random.gauss(0, 0.05),
                flow_ma=12.8 + random.gauss(0, 0.1),
                pump_running=True,
                timestamp=time.time(),
            )
        elif s == "yellow_filter":
            # Filter DP approaching service threshold
            return RawSample(
                p1_ma=7.5,
                p2_ma=9.5,
                p3_ma=6.0,  # higher DP
                flow_ma=12.0,
                pump_running=True,
                timestamp=time.time(),
            )
        elif s == "red_loss_of_prime":
            # Pulsing flow + unstable suction
            pulse = math.sin(self._t * 0.3) * 3.0
            return RawSample(
                p1_ma=4.2 + abs(pulse) * 0.5,
                p2_ma=5.0,
                p3_ma=4.5,
                flow_ma=4.5 + abs(pulse),
                pump_running=True,
                timestamp=time.time(),
            )
        elif s == "red_no_flow":
            return RawSample(
                p1_ma=4.1,
                p2_ma=5.0,
                p3_ma=4.5,
                flow_ma=4.05,
                pump_running=True,
                timestamp=time.time(),
            )
        elif s == "fault_under":
            return RawSample(p1_ma=2.0, p2_ma=2.0, p3_ma=2.0, flow_ma=2.0, pump_running=False, timestamp=time.time())
        elif s == "fault_over":
            return RawSample(p1_ma=22.0, p2_ma=22.0, p3_ma=22.0, flow_ma=22.0, pump_running=True, timestamp=time.time())
        elif s == "invalid_p3_p2":
            return RawSample(p1_ma=7.5, p2_ma=7.0, p3_ma=9.0, flow_ma=12.0, pump_running=True, timestamp=time.time())
        else:
            # Default green
            return RawSample(p1_ma=8.0, p2_ma=9.0, p3_ma=7.5, flow_ma=12.0, pump_running=True, timestamp=time.time())


def build_adapter(cfg: DeviceConfig) -> SensorAdapter:
    if cfg.sensor_adapter == "sequent":
        return SequentAdapter()
    scenario = __import__("os").getenv("SIM_SCENARIO", "green")
    return SimulatorAdapter(scenario=scenario)
