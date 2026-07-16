"""Telemetry aggregation — convert per-second raw samples into a one-minute summary."""
from __future__ import annotations
import statistics
from datetime import datetime, timezone
from typing import Any

from .config import DeviceConfig
from .quality import classify, QualityState
from .scaling import ma_to_eu


# ----- internal type alias -----
# A RawSample-compatible dict or object with p1_ma, p2_ma, p3_ma, flow_ma,
# pump_running, timestamp attributes.


def _stats(vals: list[float]) -> tuple[float, float, float, float]:
    avg = statistics.mean(vals)
    mn = min(vals)
    mx = max(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    return round(avg, 2), round(mn, 2), round(mx, 2), round(sd, 2)


def summarise(samples: list[Any], cfg: DeviceConfig) -> dict[str, Any]:
    """Convert a list of raw 1-second samples into a one-minute telemetry payload.

    Preserves raw mA values alongside EU values so quality and calibration can
    be evaluated downstream without losing the original signal.
    """
    p1_eu = [ma_to_eu(s.p1_ma, cfg.p1) for s in samples]
    p2_eu = [ma_to_eu(s.p2_ma, cfg.p2) for s in samples]
    p3_eu = [ma_to_eu(s.p3_ma, cfg.p3) for s in samples]
    flow_eu = [ma_to_eu(s.flow_ma, cfg.flow) for s in samples]

    pump_on = sum(1 for s in samples if s.pump_running) > len(samples) / 2

    p1_avg, p1_min, p1_max, _ = _stats(p1_eu)
    p2_avg, p2_min, p2_max, _ = _stats(p2_eu)
    p3_avg, p3_min, p3_max, _ = _stats(p3_eu)
    fl_avg, fl_min, fl_max, fl_sd = _stats(flow_eu)

    p1_ma_avg = round(statistics.mean(s.p1_ma for s in samples), 3)
    p2_ma_avg = round(statistics.mean(s.p2_ma for s in samples), 3)
    p3_ma_avg = round(statistics.mean(s.p3_ma for s in samples), 3)
    fl_ma_avg = round(statistics.mean(s.flow_ma for s in samples), 3)

    observed = datetime.fromtimestamp(samples[-1].timestamp, tz=timezone.utc).isoformat()

    # Near-zero flow count (for pulsing detection)
    near_zero_count = sum(1 for v in flow_eu if v < 5.0)
    cv = round(fl_sd / max(fl_avg, 0.1), 4)

    return {
        "device_id": cfg.device_id,
        "trial_phase": cfg.trial_phase,
        "trial_run_id": cfg.trial_run_id,
        "observed_at": observed,
        "sample_period_sec": len(samples),
        "samples": len(samples),
        "pump_running": pump_on,
        "p1_suction_psi_avg": p1_avg,
        "p1_suction_psi_min": p1_min,
        "p1_suction_psi_max": p1_max,
        "p2_filter_inlet_psi_avg": p2_avg,
        "p2_filter_inlet_psi_min": p2_min,
        "p2_filter_inlet_psi_max": p2_max,
        "p3_filter_outlet_psi_avg": p3_avg,
        "p3_filter_outlet_psi_min": p3_min,
        "p3_filter_outlet_psi_max": p3_max,
        "filter_dp_psi_avg": round(p2_avg - p3_avg, 2),
        "flow_gpm_avg": fl_avg,
        "flow_gpm_min": fl_min,
        "flow_gpm_max": fl_max,
        "flow_gpm_stddev": fl_sd,
        "flow_near_zero_count": near_zero_count,
        "flow_cv": cv,
        "raw_ma": {
            "p1_avg": p1_ma_avg,
            "p2_avg": p2_ma_avg,
            "p3_avg": p3_ma_avg,
            "flow_avg": fl_ma_avg,
        },
        "quality": {
            "p1": classify(p1_ma_avg).value,
            "p2": classify(p2_ma_avg).value,
            "p3": classify(p3_ma_avg).value,
            "flow": classify(fl_ma_avg).value,
        },
    }
