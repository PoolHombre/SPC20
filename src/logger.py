from __future__ import annotations
import logging
import math
import statistics
import time
from datetime import datetime, timezone
from typing import Any

from .config import DeviceConfig, load_config
from .heuristics import evaluate
from .ingest_client import IngestClient
from .local_buffer import LocalBuffer
from .sensors import RawSample, SensorAdapter, build_adapter, ma_to_eu, quality


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )


def _summarise(samples: list[RawSample], cfg: DeviceConfig) -> dict[str, Any]:
    """Convert a list of raw 1-second samples into a one-minute telemetry payload."""
    p1_eu = [ma_to_eu(s.p1_ma, cfg.p1) for s in samples]
    p2_eu = [ma_to_eu(s.p2_ma, cfg.p2) for s in samples]
    p3_eu = [ma_to_eu(s.p3_ma, cfg.p3) for s in samples]
    flow_eu = [ma_to_eu(s.flow_ma, cfg.flow) for s in samples]

    pump_on = sum(1 for s in samples if s.pump_running) > len(samples) / 2

    def _stats(vals: list[float]) -> tuple[float, float, float, float]:
        avg = statistics.mean(vals)
        mn = min(vals)
        mx = max(vals)
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return round(avg, 2), round(mn, 2), round(mx, 2), round(sd, 2)

    p1_avg, p1_min, p1_max, _ = _stats(p1_eu)
    p2_avg, p2_min, p2_max, _ = _stats(p2_eu)
    p3_avg, p3_min, p3_max, _ = _stats(p3_eu)
    fl_avg, fl_min, fl_max, fl_sd = _stats(flow_eu)

    observed = datetime.fromtimestamp(samples[-1].timestamp, tz=timezone.utc).isoformat()

    return {
        "device_id": cfg.device_id,
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
        "raw_ma": {
            "p1_avg": round(statistics.mean(s.p1_ma for s in samples), 3),
            "p2_avg": round(statistics.mean(s.p2_ma for s in samples), 3),
            "p3_avg": round(statistics.mean(s.p3_ma for s in samples), 3),
            "flow_avg": round(statistics.mean(s.flow_ma for s in samples), 3),
        },
        "quality": {
            "p1": quality(statistics.mean(s.p1_ma for s in samples)),
            "p2": quality(statistics.mean(s.p2_ma for s in samples)),
            "p3": quality(statistics.mean(s.p3_ma for s in samples)),
            "flow": quality(statistics.mean(s.flow_ma for s in samples)),
        },
    }


def run() -> None:
    cfg = load_config()
    _setup_logging(cfg.log_level)
    log = logging.getLogger("spc20.logger")

    adapter: SensorAdapter = build_adapter(cfg)
    buffer = LocalBuffer(cfg.db_path)
    client = IngestClient(cfg)

    log.info("SPC 2.0 logger starting — device=%s adapter=%s", cfg.device_id, cfg.sensor_adapter)

    samples: list[RawSample] = []
    next_summary = time.monotonic() + cfg.summary_interval_sec

    while True:
        try:
            sample = adapter.read()
            samples.append(sample)
        except Exception as exc:
            log.error("Sensor read error: %s", exc)

        if time.monotonic() >= next_summary and samples:
            payload = _summarise(samples, cfg)
            result = evaluate(payload, cfg)
            log.info(
                "Summary %s | %s %s | %s",
                payload["observed_at"],
                result.status,
                result.action,
                result.summary,
            )
            row_id = buffer.enqueue(payload)

            # Attempt upload; then flush queue
            if client.post(payload):
                buffer.mark_uploaded(row_id)
            else:
                log.warning("Upload failed — buffered row %d", row_id)

            # Retry pending rows
            for row in buffer.pending():
                if client.post(dict(__import__("json").loads(row["payload"]))):
                    buffer.mark_uploaded(row["id"])

            samples = []
            next_summary = time.monotonic() + cfg.summary_interval_sec

        time.sleep(cfg.sample_interval_sec)


if __name__ == "__main__":
    run()
