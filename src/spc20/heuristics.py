"""Dispatch heuristics — classify telemetry summaries as GREEN / YELLOW / RED.

Priority order (first match wins):
  1. Data/measurement validity (quality flags, freshness)
  2. Pump-running state context
  3. Immediate equipment-risk patterns (RED)
  4. Severe circulation loss (RED)
  5. Hard pressure / filter limits (RED)
  6. Predictive route-today maintenance (YELLOW)
  7. Slowly degrading trends (YELLOW)
  8. GREEN normal

GREEN is only emitted when ALL of the following hold:
  - Data is fresh
  - All quality flags are GOOD or only warning-level
  - Pump is running normally
  - Flow is stable and adequate
  - P2 below hard limit
  - P3 < P2 (with tolerance) while pump running
  - Filter DP below warning threshold
  - No predicted service within the warning window
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from .config import DeviceConfig
from .quality import QualityState, is_faulted


@dataclass
class DispatchResult:
    dispatch_status: str          # GREEN | YELLOW | RED
    dispatch_action: str          # NO_VISIT | ROUTE_TODAY | SEND_NOW
    reason: str                   # machine-readable reason code
    confidence: float             # 0.0–1.0
    summary: str                  # human-readable one-liner
    recommended_first_checks: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    # Legacy aliases so existing code using .status / .action still works
    @property
    def status(self) -> str:
        return self.dispatch_status

    @property
    def action(self) -> str:
        return self.dispatch_action


def _red(
    reason: str,
    summary: str,
    evidence: dict[str, Any],
    checks: list[str] | None = None,
    confidence: float = 0.95,
) -> DispatchResult:
    return DispatchResult(
        dispatch_status="RED",
        dispatch_action="SEND_NOW",
        reason=reason,
        confidence=confidence,
        summary=summary,
        recommended_first_checks=checks or [],
        evidence=evidence,
    )


def _yellow(
    reason: str,
    summary: str,
    evidence: dict[str, Any],
    checks: list[str] | None = None,
    confidence: float = 0.90,
) -> DispatchResult:
    return DispatchResult(
        dispatch_status="YELLOW",
        dispatch_action="ROUTE_TODAY",
        reason=reason,
        confidence=confidence,
        summary=summary,
        recommended_first_checks=checks or [],
        evidence=evidence,
    )


def _green(evidence: dict[str, Any]) -> DispatchResult:
    return DispatchResult(
        dispatch_status="GREEN",
        dispatch_action="NO_VISIT",
        reason="ALL_NORMAL",
        confidence=1.0,
        summary="Flow, pressure, and filter are within normal parameters. No visit needed.",
        recommended_first_checks=[],
        evidence=evidence,
    )


def evaluate(summary: dict[str, Any], cfg: DeviceConfig) -> DispatchResult:
    """Evaluate one-minute telemetry summary and return a dispatch result."""
    ev: dict[str, Any] = {}

    pump = summary.get("pump_running", False)
    flow_avg = summary.get("flow_gpm_avg", 0.0)
    flow_min = summary.get("flow_gpm_min", 0.0)
    flow_max = summary.get("flow_gpm_max", 0.0)
    flow_stddev = summary.get("flow_gpm_stddev", 0.0)
    flow_cv = summary.get("flow_cv", 0.0)
    near_zero_count = summary.get("flow_near_zero_count", 0)
    p1_avg = summary.get("p1_suction_psi_avg", 0.0)
    p2_avg = summary.get("p2_filter_inlet_psi_avg", 0.0)
    p3_avg = summary.get("p3_filter_outlet_psi_avg", 0.0)
    dp = summary.get("filter_dp_psi_avg", 0.0)
    quality: dict[str, str] = summary.get("quality", {})

    ev.update({
        "pump_running": pump,
        "flow_gpm_avg": flow_avg,
        "flow_gpm_min": flow_min,
        "flow_gpm_max": flow_max,
        "flow_gpm_stddev": flow_stddev,
        "flow_cv": flow_cv,
        "near_zero_count": near_zero_count,
        "p1_avg": p1_avg,
        "p2_avg": p2_avg,
        "p3_avg": p3_avg,
        "dp_psi": dp,
    })

    # ── Priority 1: Sensor loop faults while pump is running ─────────────────
    # We can't verify circulation if the measurement chain is broken.
    faulted_channels = [
        ch for ch, q in quality.items()
        if is_faulted(QualityState(q)) if q in QualityState._value2member_map_
    ]
    if faulted_channels and pump:
        return _red(
            "SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION",
            f"Loop fault on channel(s) {faulted_channels} — cannot verify circulation while pump is running.",
            {**ev, "faulted_channels": faulted_channels},
            checks=[
                "Inspect wiring and connectors on faulted channel(s).",
                "Check transmitter supply voltage.",
                "Verify 250 Ω burden resistor is in circuit.",
            ],
        )

    # ── Priority 3/4: Loss of prime / suction starvation (RED) ───────────────
    # Pulsing flow at low average = pump is cavitating or losing suction.
    min_flow_threshold = cfg.required_flow_gpm * (cfg.low_flow_red_threshold_percent / 100.0)

    if pump and flow_avg < min_flow_threshold:
        # Pulsing detection: high CV, high stddev, or repeated near-zero samples
        is_pulsing = (
            flow_stddev > 10.0
            or (flow_avg > 0 and flow_cv > 0.3)
            or near_zero_count > 5
        )
        if is_pulsing:
            return _red(
                "LOW_WATER_LOSING_PRIME",
                (
                    f"Pump running but flow is pulsing "
                    f"(avg={flow_avg:.0f} GPM, stddev={flow_stddev:.1f}, cv={flow_cv:.2f}). "
                    "Likely low water, suction starvation, or loss of prime."
                ),
                {**ev},
                checks=[
                    "Check pool water level — fill if low.",
                    "Inspect skimmer baskets and pump strainer.",
                    "Check suction valves are fully open.",
                    "Inspect for air leaks on suction side.",
                ],
            )
        # No-flow, no pulsing — blocked or seized
        return _red(
            "NO_FLOW_PUMP_ON",
            f"Pump running but flow avg={flow_avg:.0f} GPM is below {min_flow_threshold:.0f} GPM threshold.",
            {**ev},
            checks=[
                "Verify pump is actually running (not just relay signal).",
                "Check for blocked discharge or closed valve.",
                "Inspect pump impeller for debris.",
            ],
        )

    # ── Priority 5: Hard pressure limits (RED) ────────────────────────────────
    if p2_avg > cfg.p2_max_psi:
        return _red(
            "HIGH_PRESSURE_OR_BLOCKED_FILTER",
            f"P2 filter inlet pressure {p2_avg:.1f} PSI exceeds hard limit {cfg.p2_max_psi:.0f} PSI.",
            {**ev},
            checks=[
                "Backwash or clean filter immediately.",
                "Verify discharge valve is open.",
                "Check for blocked return lines.",
            ],
        )

    if dp > cfg.filter_dp_hard_limit_psi:
        return _red(
            "HIGH_PRESSURE_OR_BLOCKED_FILTER",
            f"Filter differential pressure {dp:.1f} PSI exceeds hard limit {cfg.filter_dp_hard_limit_psi:.0f} PSI.",
            {**ev},
            checks=[
                "Backwash filter immediately.",
                "Do not run pump at this pressure — risk of media blowout.",
            ],
        )

    # ── Priority 3: Invalid P3 >= P2 (RED) ───────────────────────────────────
    # Only fire when pump is running and P2 is measurably above zero.
    # Guard prevents false trips at pump-off static-head conditions.
    tolerance = cfg.calibration_p23_tolerance_psi
    if pump and p2_avg > 0 and (p3_avg - p2_avg) >= tolerance:
        return _red(
            "INVALID_PRESSURE_RELATIONSHIP",
            (
                f"P3 ({p3_avg:.1f} PSI) >= P2 ({p2_avg:.1f} PSI) + tolerance ({tolerance:.1f} PSI) "
                "while pump is running — filter or pressure sensor problem."
            ),
            {**ev},
            checks=[
                "Verify P2 and P3 sensor wiring is not swapped.",
                "Inspect check valve between P2 and P3 taps.",
                "Confirm filter is not bypassed.",
            ],
        )

    # ── Priority 6: Predictive YELLOW — filter service ────────────────────────
    if dp >= cfg.filter_service_dp_psi:
        return _yellow(
            "FILTER_SERVICE_SOON",
            f"Filter DP={dp:.1f} PSI is at or above service threshold ({cfg.filter_service_dp_psi} PSI). Backwash today.",
            {**ev},
            checks=["Schedule backwash/cleaning. Note before/after DP."],
        )

    if dp >= cfg.filter_clean_dp_psi * 1.5:
        return _yellow(
            "FILTER_LOADING_HIGH",
            f"Filter DP={dp:.1f} PSI is elevated. Service likely needed within 24 hours.",
            {**ev},
            checks=["Monitor closely. Plan backwash for today's route."],
        )

    # ── Priority 7: Degrading trends (YELLOW) ────────────────────────────────
    if pump and flow_avg < cfg.normal_flow_gpm_min:
        return _yellow(
            "FLOW_DECLINING",
            f"Flow avg={flow_avg:.0f} GPM is below normal minimum ({cfg.normal_flow_gpm_min:.0f} GPM). Trending down.",
            {**ev},
            checks=[
                "Inspect skimmer baskets.",
                "Check filter DP trend.",
                "Inspect suction-side valves.",
            ],
        )

    # ── Priority 8: GREEN ─────────────────────────────────────────────────────
    return _green(ev)
