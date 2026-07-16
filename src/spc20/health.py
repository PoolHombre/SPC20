"""Device health status aggregation."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class HealthStatus:
    device_id: str
    software_version: str
    trial_phase: str
    trial_run_id: str
    local_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    db_path: str = ""
    db_integrity_ok: bool = True
    db_integrity_detail: str = "ok"
    upload_queue_depth: int = 0
    last_upload_time: Optional[str] = None
    internet_reachable: Optional[bool] = None
    uptime_seconds: float = 0.0

    def as_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "software_version": self.software_version,
            "trial_phase": self.trial_phase,
            "trial_run_id": self.trial_run_id,
            "local_time": self.local_time,
            "db_path": self.db_path,
            "db_integrity_ok": self.db_integrity_ok,
            "db_integrity_detail": self.db_integrity_detail,
            "upload_queue_depth": self.upload_queue_depth,
            "last_upload_time": self.last_upload_time,
            "internet_reachable": self.internet_reachable,
            "uptime_seconds": self.uptime_seconds,
        }
