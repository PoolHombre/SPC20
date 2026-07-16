from __future__ import annotations
import logging

import httpx

from .config import DeviceConfig

log = logging.getLogger(__name__)


class IngestClient:
    def __init__(self, cfg: DeviceConfig) -> None:
        self._url = cfg.supabase_url
        self._headers = {
            "x-device-id": cfg.device_id,
            "x-device-token": cfg.device_token,
            "Content-Type": "application/json",
        }

    def post(self, payload: dict, timeout: float = 10.0) -> bool:
        try:
            r = httpx.post(self._url, json=payload, headers=self._headers, timeout=timeout)
            r.raise_for_status()
            log.debug("Uploaded %s — %s", payload.get("observed_at"), r.status_code)
            return True
        except Exception as exc:
            log.warning("Upload failed: %s", exc)
            return False
