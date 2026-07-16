from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SensorRange:
    min_ma: float = 4.0
    max_ma: float = 20.0
    min_eu: float = 0.0
    max_eu: float = 100.0


@dataclass
class DeviceConfig:
    device_id: str = field(default_factory=lambda: os.environ["DEVICE_ID"])
    device_token: str = field(default_factory=lambda: os.environ["DEVICE_TOKEN"])
    supabase_url: str = field(default_factory=lambda: os.environ["SUPABASE_INGEST_URL"])
    sensor_adapter: str = field(default_factory=lambda: os.getenv("SENSOR_ADAPTER", "simulator"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # P1 suction: compound/vacuum capable, e.g. -15 to +15 PSI
    p1: SensorRange = field(default_factory=lambda: SensorRange(min_eu=-15.0, max_eu=15.0))
    # P2 filter inlet: 0–100 PSI
    p2: SensorRange = field(default_factory=lambda: SensorRange(min_eu=0.0, max_eu=100.0))
    # P3 filter outlet: 0–100 PSI
    p3: SensorRange = field(default_factory=lambda: SensorRange(min_eu=0.0, max_eu=100.0))
    # Flow: 0–500 GPM (set per-site)
    flow: SensorRange = field(default_factory=lambda: SensorRange(min_eu=0.0, max_eu=500.0))

    # Pool/filter thresholds
    required_flow_gpm: float = 300.0
    normal_flow_gpm_min: float = 280.0
    normal_flow_gpm_max: float = 380.0
    filter_clean_dp_psi: float = 5.0
    filter_service_dp_psi: float = 12.0
    filter_warning_hours: float = 24.0
    low_flow_red_threshold_percent: float = 20.0
    red_confirm_seconds: int = 60
    stale_data_red_minutes: int = 10

    db_path: str = "spc20_buffer.db"
    sample_interval_sec: float = 1.0
    summary_interval_sec: float = 60.0


def load_config() -> DeviceConfig:
    return DeviceConfig()
