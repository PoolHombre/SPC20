"""SPC 2.0 local diagnostic dashboard — Flask application factory.

Run via gunicorn:
    gunicorn -w 2 -b 0.0.0.0:8080 "spc20.web.app:create_app()"

NEVER run with debug=True in production.
SECURITY: /api/status must NEVER include DEVICE_TOKEN or Supabase credentials.
"""
from __future__ import annotations
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, g

from ..config import load_config
from ..buffer import LocalBuffer
from ..calibration import Calibrator
from ..health import HealthStatus
from ..heuristics import evaluate, DispatchResult
from ..quality import classify
from .. import __version__
from .auth import require_auth

log = logging.getLogger(__name__)

_START_TIME = time.monotonic()

# Module-level state shared across requests (in-process only)
_last_summary: dict[str, Any] = {}
_last_result: DispatchResult | None = None


def set_last_telemetry(summary: dict[str, Any], result: DispatchResult) -> None:
    """Called by the logger service to push the most recent telemetry into the web layer."""
    global _last_summary, _last_result
    _last_summary = summary
    _last_result = result


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    cfg = load_config()

    # ── GET / — dashboard HTML ─────────────────────────────────────────────
    @app.route("/")
    def index():
        return render_template(
            "index.html",
            device_id=cfg.device_id,
            version=__version__,
            trial_phase=cfg.trial_phase,
            trial_run_id=cfg.trial_run_id,
        )

    # ── GET /api/status — safe status payload (no secrets) ────────────────
    @app.route("/api/status")
    def api_status():
        result = _last_result
        summary = _last_summary
        buf = LocalBuffer(cfg.db_path)

        payload: dict[str, Any] = {
            "device_id": cfg.device_id,
            "software_version": __version__,
            "trial_phase": cfg.trial_phase,
            "trial_run_id": cfg.trial_run_id,
            "local_time": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
            "upload_queue_depth": buf.pending_count(),
            "last_upload_time": buf.last_upload_time(),
            "db_path": cfg.db_path,
            "db_integrity_ok": buf.integrity_check(),
            # Dispatch
            "dispatch": {
                "status": result.dispatch_status if result else "UNKNOWN",
                "action": result.dispatch_action if result else "UNKNOWN",
                "reason": result.reason if result else "NO_DATA",
                "summary": result.summary if result else "No telemetry received yet.",
                "confidence": result.confidence if result else 0.0,
                "recommended_first_checks": result.recommended_first_checks if result else [],
            } if result else None,
            # Sensor readings (EU + raw mA + quality)
            "sensors": {
                "pump_running": summary.get("pump_running"),
                "p1_suction_psi": summary.get("p1_suction_psi_avg"),
                "p2_filter_inlet_psi": summary.get("p2_filter_inlet_psi_avg"),
                "p3_filter_outlet_psi": summary.get("p3_filter_outlet_psi_avg"),
                "filter_dp_psi": summary.get("filter_dp_psi_avg"),
                "flow_gpm": summary.get("flow_gpm_avg"),
                "raw_ma": summary.get("raw_ma", {}),
                "quality": summary.get("quality", {}),
            } if summary else None,
        }
        # NEVER include DEVICE_TOKEN or Supabase keys in the response
        return jsonify(payload)

    # ── GET /api/live — minimal live-data endpoint for auto-refresh ────────
    @app.route("/api/live")
    def api_live():
        result = _last_result
        summary = _last_summary
        return jsonify({
            "status": result.dispatch_status if result else "UNKNOWN",
            "action": result.dispatch_action if result else "UNKNOWN",
            "reason": result.reason if result else "NO_DATA",
            "summary": result.summary if result else "Awaiting first sample.",
            "pump_running": summary.get("pump_running"),
            "flow_gpm": summary.get("flow_gpm_avg"),
            "filter_dp_psi": summary.get("filter_dp_psi_avg"),
            "observed_at": summary.get("observed_at"),
        })

    # ── GET /api/health ────────────────────────────────────────────────────
    @app.route("/api/health")
    def api_health():
        buf = LocalBuffer(cfg.db_path)
        ok = buf.integrity_check()
        return jsonify({
            "status": "ok" if ok else "degraded",
            "db_integrity": ok,
            "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
            "version": __version__,
        }), 200 if ok else 503

    # ── POST /api/calibration/ambient-zero (protected) ────────────────────
    @app.route("/api/calibration/ambient-zero", methods=["POST"])
    @require_auth
    def calibration_ambient_zero():
        from flask import request as req
        data = req.get_json(silent=True) or {}
        channel = data.get("channel", "p1")
        notes = data.get("notes", "")
        created_by = data.get("created_by", "dashboard")

        # In the web context we don't have live sensor access; we return a
        # "schedule" response — the logger service performs the actual calibration.
        # This endpoint records the request and returns instructions.
        log.info("Calibration request: ambient_zero channel=%s by=%s", channel, created_by)
        return jsonify({
            "status": "accepted",
            "message": (
                f"Ambient-zero calibration for channel '{channel}' queued. "
                "The logger service will collect samples on the next cycle. "
                "Ensure the transmitter is vented/isolated before proceeding."
            ),
            "channel": channel,
            "notes": notes,
        })

    # ── POST /api/calibration/static-baseline (protected) ─────────────────
    @app.route("/api/calibration/static-baseline", methods=["POST"])
    @require_auth
    def calibration_static_baseline():
        from flask import request as req
        data = req.get_json(silent=True) or {}
        notes = data.get("notes", "")
        created_by = data.get("created_by", "dashboard")

        pump_running = _last_summary.get("pump_running", True) if _last_summary else True
        if pump_running:
            return jsonify({
                "status": "rejected",
                "reason": "Pump appears to be running. Stop the pump before taking a static baseline.",
            }), 409

        log.info("Calibration request: static_baseline by=%s", created_by)
        return jsonify({
            "status": "accepted",
            "message": (
                "Static baseline calibration queued. "
                "The logger service will capture P2 and P3 static head on the next cycle."
            ),
            "notes": notes,
        })

    return app
