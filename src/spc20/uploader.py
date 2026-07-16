"""Supabase ingest client — sends telemetry payloads via device token auth.

SECURITY: This module must NEVER log or expose the DEVICE_TOKEN or any
Supabase credentials. The service role key must never appear on the device.
"""
from __future__ import annotations
import logging

import httpx

from .config import DeviceConfig

log = logging.getLogger(__name__)


class IngestClient:
    def __init__(self, cfg: DeviceConfig) -> None:
        self._url = cfg.supabase_url
        # Headers include device token (per-device credential, not the service role key)
        self._headers = {
            "x-device-id": cfg.device_id,
            "x-device-token": cfg.device_token,
            "Content-Type": "application/json",
        }
        self._reachable: bool | None = None

    def post(self, payload: dict, timeout: float = 10.0) -> bool:
        try:
            r = httpx.post(self._url, json=payload, headers=self._headers, timeout=timeout)
            r.raise_for_status()
            self._reachable = True
            log.debug("Uploaded %s — %s", payload.get("observed_at"), r.status_code)
            return True
        except Exception as exc:
            self._reachable = False
            log.warning("Upload failed: %s", exc)
            return False

    @property
    def last_reachable(self) -> bool | None:
        """None = never attempted. True/False = result of last attempt."""
        return self._reachable
