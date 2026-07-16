"""Sensor adapters — abstract base, simulator, and Sequent HAT."""
from .base import SensorAdapter, RawSample
from .simulator import SimulatorAdapter
from .sequent import SequentAdapter
from ..config import DeviceConfig


def build_adapter(cfg: DeviceConfig) -> SensorAdapter:
    if cfg.sensor_adapter == "sequent":
        return SequentAdapter()
    import os
    scenario = os.getenv("SIM_SCENARIO", "green")
    return SimulatorAdapter(scenario=scenario)


__all__ = ["SensorAdapter", "RawSample", "SimulatorAdapter", "SequentAdapter", "build_adapter"]
