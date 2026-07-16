"""Sensor calibration — ambient-zero and static-baseline modes.

Calibration offsets are stored in a local SQLite table and applied
before heuristic calculations. Raw mA values are always preserved.

Mode A — ambient_zero:
    Technician confirms the transmitter is vented / isolated from process.
    Collects 30–60 seconds of samples at known-zero pressure.
    Rejects if stddev exceeds the configured threshold.
    Stores the mean as an offset applied to future readings.

Mode B — static_baseline:
    Used when pump_running == False.
    Captures the P2 and P3 static-head values.
    Stores p2_static_mean, p3_static_mean, and their difference
    (static_p23_offset) for differential-pressure reference.
"""
from __future__ import annotations
import sqlite3
import statistics
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Generator, Optional

from .config import DeviceConfig
from .scaling import ma_to_eu


CREATE_CALIBRATION_TABLE = """
CREATE TABLE IF NOT EXISTS calibration_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id           TEXT NOT NULL,
    trial_phase         TEXT,
    trial_run_id        TEXT,
    channel             TEXT NOT NULL,
    mode                TEXT NOT NULL,
    offset_value        REAL,
    units               TEXT,
    sample_count        INTEGER,
    sample_duration_sec REAL,
    mean                REAL,
    stddev              REAL,
    min_value           REAL,
    max_value           REAL,
    created_at          TEXT DEFAULT (datetime('now')),
    created_by          TEXT,
    notes               TEXT,
    uploaded_at         TEXT
);
"""


@dataclass
class CalibrationResult:
    channel: str
    mode: str
    offset_value: Optional[float]
    units: str
    mean: float
    stddev: float
    min_value: float
    max_value: float
    sample_count: int
    sample_duration_sec: float
    accepted: bool
    rejection_reason: Optional[str] = None
    # For static_baseline mode:
    p2_static_mean: Optional[float] = None
    p3_static_mean: Optional[float] = None
    static_p23_offset: Optional[float] = None


@contextmanager
def _conn(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _ensure_table(db_path: str) -> None:
    with _conn(db_path) as con:
        con.executescript(CREATE_CALIBRATION_TABLE)


def _store_event(
    db_path: str,
    result: CalibrationResult,
    device_id: str,
    trial_phase: str,
    trial_run_id: str,
    created_by: str,
    notes: str = "",
) -> None:
    with _conn(db_path) as con:
        con.execute(
            """INSERT INTO calibration_events
               (device_id, trial_phase, trial_run_id, channel, mode,
                offset_value, units, sample_count, sample_duration_sec,
                mean, stddev, min_value, max_value, created_by, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                device_id,
                trial_phase,
                trial_run_id,
                result.channel,
                result.mode,
                result.offset_value,
                result.units,
                result.sample_count,
                result.sample_duration_sec,
                result.mean,
                result.stddev,
                result.min_value,
                result.max_value,
                created_by,
                notes,
            ),
        )


class Calibrator:
    """Run calibration procedures and persist results to SQLite."""

    def __init__(self, cfg: DeviceConfig) -> None:
        self._cfg = cfg
        _ensure_table(cfg.db_path)

    def ambient_zero(
        self,
        read_channel_ma: Callable[[], float],
        channel: str,
        created_by: str = "technician",
        notes: str = "",
    ) -> CalibrationResult:
        """Mode A: collect samples at known-zero, compute offset.

        Args:
            read_channel_ma: callable that returns the current mA reading for the channel.
            channel: channel name, e.g. "p1", "p2", "p3".
            created_by: operator identifier.
            notes: free-form notes for this calibration event.

        Returns:
            CalibrationResult with accepted=True if stddev within threshold,
            accepted=False with rejection_reason otherwise.
        """
        cfg = self._cfg
        target_seconds = cfg.calibration_sample_seconds
        samples: list[float] = []
        t_start = time.monotonic()

        while (time.monotonic() - t_start) < target_seconds:
            samples.append(read_channel_ma())
            time.sleep(cfg.sample_interval_sec)

        duration = time.monotonic() - t_start
        mean = statistics.mean(samples)
        sd = statistics.stdev(samples) if len(samples) > 1 else 0.0
        mn = min(samples)
        mx = max(samples)

        accepted = sd <= cfg.calibration_stddev_limit
        rejection_reason: Optional[str] = None
        if not accepted:
            rejection_reason = (
                f"Stddev {sd:.4f} mA exceeds limit {cfg.calibration_stddev_limit:.4f} mA — "
                "transmitter may not be fully isolated or signal is noisy."
            )

        result = CalibrationResult(
            channel=channel,
            mode="ambient_zero",
            offset_value=-mean if accepted else None,  # subtract mean to zero out reading
            units="mA",
            mean=mean,
            stddev=sd,
            min_value=mn,
            max_value=mx,
            sample_count=len(samples),
            sample_duration_sec=round(duration, 1),
            accepted=accepted,
            rejection_reason=rejection_reason,
        )

        _store_event(
            cfg.db_path, result,
            cfg.device_id, cfg.trial_phase, cfg.trial_run_id,
            created_by, notes,
        )
        return result

    def static_baseline(
        self,
        read_p2_ma: Callable[[], float],
        read_p3_ma: Callable[[], float],
        pump_running: bool,
        created_by: str = "technician",
        notes: str = "",
    ) -> CalibrationResult:
        """Mode B: capture static head values with pump off.

        Captures P2 and P3 static-head values and computes their differential.
        Raises ValueError if pump_running is True — static baseline is only valid
        when the pump is confirmed off.

        Returns:
            CalibrationResult for P2, and also stores a P3 event.
            The static_p23_offset field contains (p2_mean - p3_mean).
        """
        if pump_running:
            raise ValueError(
                "static_baseline requires pump_running == False. "
                "Stop the pump before running this calibration mode."
            )

        cfg = self._cfg
        target_seconds = cfg.calibration_sample_seconds
        p2_samples: list[float] = []
        p3_samples: list[float] = []
        t_start = time.monotonic()

        while (time.monotonic() - t_start) < target_seconds:
            p2_samples.append(read_p2_ma())
            p3_samples.append(read_p3_ma())
            time.sleep(cfg.sample_interval_sec)

        duration = time.monotonic() - t_start

        p2_mean = statistics.mean(p2_samples)
        p3_mean = statistics.mean(p3_samples)
        p2_sd = statistics.stdev(p2_samples) if len(p2_samples) > 1 else 0.0
        p3_sd = statistics.stdev(p3_samples) if len(p3_samples) > 1 else 0.0

        static_p23_offset = p2_mean - p3_mean
        accepted = True  # static baseline always accepted (pump-off guarantees)

        result = CalibrationResult(
            channel="p2_p3_static",
            mode="static_baseline",
            offset_value=static_p23_offset,
            units="mA",
            mean=p2_mean,
            stddev=p2_sd,
            min_value=min(p2_samples),
            max_value=max(p2_samples),
            sample_count=len(p2_samples),
            sample_duration_sec=round(duration, 1),
            accepted=accepted,
            p2_static_mean=p2_mean,
            p3_static_mean=p3_mean,
            static_p23_offset=static_p23_offset,
        )

        # Store P2 event
        _store_event(
            cfg.db_path, result,
            cfg.device_id, cfg.trial_phase, cfg.trial_run_id,
            created_by, f"P2 static baseline. {notes}",
        )

        # Store P3 event separately
        p3_result = CalibrationResult(
            channel="p3",
            mode="static_baseline",
            offset_value=None,
            units="mA",
            mean=p3_mean,
            stddev=p3_sd,
            min_value=min(p3_samples),
            max_value=max(p3_samples),
            sample_count=len(p3_samples),
            sample_duration_sec=round(duration, 1),
            accepted=True,
        )
        _store_event(
            cfg.db_path, p3_result,
            cfg.device_id, cfg.trial_phase, cfg.trial_run_id,
            created_by, f"P3 static baseline. {notes}",
        )

        return result

    def get_active_offsets(self) -> dict[str, float]:
        """Return the most recent accepted offset for each channel, in mA."""
        offsets: dict[str, float] = {}
        with _conn(self._cfg.db_path) as con:
            rows = con.execute(
                """SELECT channel, offset_value
                   FROM calibration_events
                   WHERE offset_value IS NOT NULL
                   ORDER BY id DESC"""
            ).fetchall()
        seen: set[str] = set()
        for row in rows:
            if row["channel"] not in seen:
                offsets[row["channel"]] = row["offset_value"]
                seen.add(row["channel"])
        return offsets
