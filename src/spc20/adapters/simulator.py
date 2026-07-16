"""Simulator adapter — generates synthetic 4-20 mA samples for bench testing."""
from __future__ import annotations
import math
import random
import time

from .base import RawSample, SensorAdapter


class SimulatorAdapter(SensorAdapter):
    """Generates synthetic 4-20 mA samples. Scenario driven by argument or SIM_SCENARIO env."""

    SCENARIOS = [
        "green",
        "yellow_filter",
        "red_loss_of_prime",
        "red_no_flow",
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
            return RawSample(
                p1_ma=7.5,
                p2_ma=9.5,
                p3_ma=6.0,
                flow_ma=12.0,
                pump_running=True,
                timestamp=time.time(),
            )
        elif s == "red_loss_of_prime":
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
            return RawSample(
                p1_ma=2.0, p2_ma=2.0, p3_ma=2.0, flow_ma=2.0,
                pump_running=False, timestamp=time.time(),
            )
        elif s == "fault_over":
            return RawSample(
                p1_ma=22.0, p2_ma=22.0, p3_ma=22.0, flow_ma=22.0,
                pump_running=True, timestamp=time.time(),
            )
        elif s == "invalid_p3_p2":
            return RawSample(
                p1_ma=7.5, p2_ma=7.0, p3_ma=9.0, flow_ma=12.0,
                pump_running=True, timestamp=time.time(),
            )
        else:
            return RawSample(
                p1_ma=8.0, p2_ma=9.0, p3_ma=7.5, flow_ma=12.0,
                pump_running=True, timestamp=time.time(),
            )
