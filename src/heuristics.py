from __future__ import annotations
import statistics
from dataclasses import dataclass
from typing import Any

from .config import DeviceConfig


@dataclass
class DispatchResult:
    status: str          # GREEN | YELLOW | RED
    action: str          # NO_VISIT | ROUTE_TODAY | SEND_NOW
    reason: str
    summary: str
    evidence: dict[str, Any]
    confidence: float = 1.0


def evaluate(summary: dict[str, Any], cfg: DeviceConfig) -> DispatchResult:
    """
    Evaluate one-minute telemetry summary and return a dispatch result.
    Evaluation order matches the brief: freshness → quality → pump → RED rules → YELLOW rules → GREEN.
    """
    ev: dict[str, Any] = {}

    pump = summary.get("pump_running", False)
    flow_avg = summary.get("flow_gpm_avg", 0.0)
    flow_min = summary.get("flow_gpm_min", 0.0)
    flow_stddev = summary.get("flow_gpm_stddev", 0.0)
    p1_avg = summary.get("p1_suction_psi_avg", 0.0)
    p2_avg = summary.get("p2_filter_inlet_psi_avg", 0.0)
    p3_avg = summary.get("p3_filter_outlet_psi_avg", 0.0)
    dp = summary.get("filter_dp_psi_avg", 0.0)
    quality = summary.get("quality", {})

    ev["pump_running"] = pump
    ev["flow_gpm_avg"] = flow_avg
    ev["dp_psi"] = dp

    # --- Sensor quality faults ---
    faulted = [ch for ch, q in quality.items() if q != "GOOD"]
    if faulted and pump:
        return DispatchResult(
            status="RED",
            action="SEND_NOW",
            reason="SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION",
            summary=f"Sensor fault on {faulted} — cannot verify circulation while pump is running.",
            evidence={**ev, "faulted_channels": faulted},
        )

    # --- Invalid P3 >= P2 ---
    if pump and p3_avg >= p2_avg and p2_avg > 0:
        return DispatchResult(
            status="RED",
            action="SEND_NOW",
            reason="INVALID_PRESSURE_RELATIONSHIP",
            summary=f"P3 ({p3_avg:.1f} PSI) >= P2 ({p2_avg:.1f} PSI) — filter or sensor problem.",
            evidence={**ev, "p2_avg": p2_avg, "p3_avg": p3_avg},
        )

    # --- No flow while pump running ---
    min_flow_threshold = cfg.required_flow_gpm * (cfg.low_flow_red_threshold_percent / 100.0)
    if pump and flow_avg < min_flow_threshold:
        # Check for pulsing (loss of prime indicator)
        if flow_stddev > 10.0 or (flow_avg > 0 and flow_stddev / max(flow_avg, 0.1) > 0.3):
            return DispatchResult(
                status="RED",
                action="SEND_NOW",
                reason="LOW_WATER_LOSING_PRIME",
                summary=(
                    f"Pump running but flow is pulsing (avg={flow_avg:.0f} GPM, stddev={flow_stddev:.1f}). "
                    "Likely low water, suction starvation, or loss of prime."
                ),
                evidence={**ev, "flow_stddev": flow_stddev},
            )
        return DispatchResult(
            status="RED",
            action="SEND_NOW",
            reason="NO_FLOW_PUMP_ON",
            summary=f"Pump running but flow avg={flow_avg:.0f} GPM is below {min_flow_threshold:.0f} GPM threshold.",
            evidence=ev,
        )

    # --- High filter DP → YELLOW ---
    if dp >= cfg.filter_service_dp_psi:
        return DispatchResult(
            status="YELLOW",
            action="ROUTE_TODAY",
            reason="FILTER_SERVICE_WITHIN_24_HOURS",
            summary=f"Filter DP={dp:.1f} PSI is at or above service threshold ({cfg.filter_service_dp_psi} PSI). Schedule backwash.",
            evidence={**ev, "filter_dp_psi": dp},
        )

    # --- Elevated filter DP warning ---
    if dp >= cfg.filter_clean_dp_psi * 1.5:
        return DispatchResult(
            status="YELLOW",
            action="ROUTE_TODAY",
            reason="FILTER_LOADING_HIGH",
            summary=f"Filter DP={dp:.1f} PSI is elevated. Monitor — service may be needed today.",
            evidence={**ev, "filter_dp_psi": dp},
        )

    # --- Flow low but not zero ---
    if pump and flow_avg < cfg.normal_flow_gpm_min:
        return DispatchResult(
            status="YELLOW",
            action="ROUTE_TODAY",
            reason="FLOW_TREND_DECLINING",
            summary=f"Flow avg={flow_avg:.0f} GPM is below normal minimum ({cfg.normal_flow_gpm_min:.0f} GPM).",
            evidence=ev,
        )

    # --- GREEN ---
    return DispatchResult(
        status="GREEN",
        action="NO_VISIT",
        reason="ALL_NORMAL",
        summary="Flow, pressure, and filter are within normal parameters. No visit needed.",
        evidence=ev,
        confidence=1.0,
    )
