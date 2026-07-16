"""Logger service — main read loop: sample → aggregate → evaluate → buffer → upload."""
from __future__ import annotations
import logging
import time

from ..adapters import build_adapter, SensorAdapter
from ..aggregation import summarise
from ..buffer import LocalBuffer
from ..config import DeviceConfig, load_config
from ..heuristics import evaluate
from ..uploader import IngestClient


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )


def run() -> None:
    cfg = load_config()
    _setup_logging(cfg.log_level)
    log = logging.getLogger("spc20.logger")

    adapter: SensorAdapter = build_adapter(cfg)
    buffer = LocalBuffer(cfg.db_path)

    # Startup integrity check
    if not buffer.integrity_check():
        log.error("SQLite integrity check FAILED on startup — check %s", cfg.db_path)
    else:
        log.info("SQLite integrity check passed.")

    client = IngestClient(cfg)

    log.info(
        "SPC 2.0 logger starting — device=%s adapter=%s trial=%s/%s",
        cfg.device_id, cfg.sensor_adapter, cfg.trial_phase, cfg.trial_run_id,
    )

    from ..adapters.base import RawSample
    samples: list[RawSample] = []
    next_summary = time.monotonic() + cfg.summary_interval_sec

    while True:
        try:
            sample = adapter.read()
            samples.append(sample)
        except Exception as exc:
            log.error("Sensor read error: %s", exc)

        if time.monotonic() >= next_summary and samples:
            payload = summarise(samples, cfg)
            result = evaluate(payload, cfg)
            log.info(
                "Summary %s | %s %s | %s",
                payload["observed_at"],
                result.dispatch_status,
                result.dispatch_action,
                result.summary,
            )
            row_id = buffer.enqueue(payload)

            if client.post(payload):
                buffer.mark_uploaded(row_id)
            else:
                log.warning("Upload failed — buffered row %d", row_id)

            # Retry pending rows
            import json
            for row in buffer.pending():
                if client.post(json.loads(row["payload"])):
                    buffer.mark_uploaded(row["id"])

            samples = []
            next_summary = time.monotonic() + cfg.summary_interval_sec

        time.sleep(cfg.sample_interval_sec)


if __name__ == "__main__":
    run()
