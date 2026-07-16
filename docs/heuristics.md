# Heuristics — Dispatch Rules and Reason Codes

SPC 2.0 evaluates one-minute telemetry summaries against a priority-ordered rule chain. The first matching rule determines the dispatch result. All rules are READ-ONLY — the system never controls equipment.

---

## Priority Order

1. Sensor loop faults while pump running (can't verify — RED)
2. Low flow / loss of prime while pump running (RED)
3. Hard pressure limits exceeded (RED)
4. Invalid pressure relationship P3 >= P2 (RED)
5. Filter service predictive warning (YELLOW)
6. Flow declining (YELLOW)
7. All normal (GREEN)

---

## GREEN

| Reason Code | Condition | Confidence |
|-------------|-----------|------------|
| `ALL_NORMAL` | None of the RED or YELLOW rules fired | 1.0 |

**Recommended first checks:** None — no visit needed.

---

## RED Reason Codes

### SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION

**Condition:** One or more sensor channels report LOOP_LOW_FAULT or LOOP_HIGH_FAULT while the pump is running.

**Why it fires:** Without valid sensor readings, the heuristic cannot determine whether circulation is adequate. Failure to detect a circulation problem is worse than a false alarm.

**Recommended first checks:**
- Inspect wiring and connectors on faulted channel(s).
- Check transmitter supply voltage (should be 24 VDC ± 10%).
- Verify 250 Ω burden resistor is in circuit.

**Thresholds:** LOOP_LOW_FAULT < 3.6 mA; LOOP_HIGH_FAULT > 21.0 mA.

---

### LOW_WATER_LOSING_PRIME

**Condition:** Pump running, flow_avg < 20% of required_flow_gpm, AND pulsing detected (stddev > 10 GPM OR cv > 0.3 OR near_zero_count > 5).

**Why it fires:** Pulsing flow at low average strongly indicates suction starvation — the pump is alternately cavitating and catching water. This damages the pump and halts effective filtration.

**Recommended first checks:**
- Check pool water level — fill if low.
- Inspect skimmer baskets and pump strainer.
- Check suction valves are fully open.
- Inspect for air leaks on suction side.

**Thresholds:** `required_flow_gpm × low_flow_red_threshold_percent / 100`; default = 333 × 0.20 = 66.6 GPM threshold.

---

### NO_FLOW_PUMP_ON

**Condition:** Pump running, flow_avg < threshold (same as above), NOT pulsing.

**Why it fires:** Pump is running but no flow is detected and flow is steady (not pulsing). Indicates a blocked discharge, seized impeller, or closed valve — not a priming issue.

**Recommended first checks:**
- Verify pump is actually running (not just relay signal).
- Check for blocked discharge or closed valve.
- Inspect pump impeller for debris.

---

### HIGH_PRESSURE_OR_BLOCKED_FILTER

**Condition A:** P2 filter inlet > p2_max_psi (default 80 PSI).

**Condition B:** Filter DP (P2 − P3) > filter_dp_hard_limit_psi (default 18 PSI).

**Why it fires:** High filter pressure risks media blowout (for sand/DE filters) or structural damage. This is a damage-prevention rule.

**Recommended first checks:**
- Backwash or clean filter immediately.
- Verify discharge valve is open.
- Check for blocked return lines.
- Do not run pump at this pressure — risk of media blowout (condition B).

---

### INVALID_PRESSURE_RELATIONSHIP

**Condition:** Pump running AND P2 > 0 AND (P3 − P2) >= calibration_p23_tolerance_psi (default 0.5 PSI).

**Why it fires:** P3 (filter outlet) should always be less than P2 (filter inlet) when the pump is running and the filter is in-line. P3 >= P2 violates the physics of the system and indicates a sensor wiring error, swapped sensors, or a bypassed filter.

**Guard:** This rule does NOT fire when pump_running = False. Static-head conditions can legitimately show P3 ≈ P2.

**Recommended first checks:**
- Verify P2 and P3 sensor wiring is not swapped.
- Inspect check valve between P2 and P3 taps.
- Confirm filter is not bypassed.

---

## YELLOW Reason Codes

### FILTER_SERVICE_SOON

**Condition:** Filter DP >= filter_service_dp_psi (default 12 PSI).

**Why it fires:** DP at or above the service threshold indicates the filter is loaded and should be backwashed during today's route. This is a predictive rule — the system is still circulating, but efficiency is degraded.

**Recommended first checks:**
- Schedule backwash/cleaning. Note before and after DP readings.

**Confidence:** 0.90

---

### FILTER_LOADING_HIGH

**Condition:** Filter DP >= filter_clean_dp_psi × 1.5 (default 5 × 1.5 = 7.5 PSI) but < filter_service_dp_psi.

**Why it fires:** Filter is loading faster than expected. Service likely needed within 24 hours.

**Recommended first checks:**
- Monitor closely. Plan backwash for today's route.

---

### FLOW_DECLINING

**Condition:** Pump running AND flow_avg < normal_flow_gpm_min (default 280 GPM).

**Why it fires:** Flow is below the normal operating range but above the RED threshold. This is a trend indicator — the pool is circulating but not at full efficiency. Common causes: dirty skimmer baskets, partially closed valve, early filter loading.

**Recommended first checks:**
- Inspect skimmer baskets.
- Check filter DP trend.
- Inspect suction-side valves.

---

## Configurable Thresholds

All thresholds come from DeviceConfig (environment variables or defaults):

| Parameter | Default | Env Var (not yet wired — future) |
|-----------|---------|----------------------------------|
| required_flow_gpm | 300.0 | REQUIRED_FLOW_GPM |
| normal_flow_gpm_min | 280.0 | — |
| filter_clean_dp_psi | 5.0 | — |
| filter_service_dp_psi | 12.0 | — |
| filter_dp_hard_limit_psi | 18.0 | — |
| p2_max_psi | 80.0 | P2_MAX_PSI |
| low_flow_red_threshold_percent | 20.0 | — |
| calibration_p23_tolerance_psi | 0.5 | — |
