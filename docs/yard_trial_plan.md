# Yard Trial Plan — SPC 2.0 Build 1B

## Goal

Validate that the SPC 2.0 hardware and software perform correctly in an outdoor environment with real sensors connected to a controlled pipe rig, before deploying at a customer site.

The yard trial is NOT a pool monitoring trial — it is a hardware and software qualification trial. The "pool" is a pipe/bucket rig at the Poolsure yard facility.

---

## Duration

**Target:** 5 days continuous unattended operation minimum. Extend to 10 days if any anomalies are detected.

---

## Rig Setup

- Centrifugal pump (min 2HP) connected to a recirculating pipe loop
- P1 (suction) tap on pump inlet
- P2 (filter inlet) tap on pump discharge / filter inlet
- P3 (filter outlet) tap after a real sand or cartridge filter
- Flow transmitter on the discharge line
- Pump proof current switch on motor lead
- Variable discharge valve to allow controlled flow restriction tests

---

## Data Collection Plan

| Metric | Frequency | Storage |
|--------|-----------|---------|
| All sensor readings (1 min summary) | Continuous | Local SQLite + Supabase |
| Calibration events | At start + after each transmitter disturbance | SQLite + Supabase |
| Alert events (status changes) | On every status change | Supabase dispatch result columns |
| Power cycle events | Logged manually | power_cycle_test_plan.md form |
| Weather conditions | Daily note | Yard trial log (this doc) |
| Enclosure temperature | Optionally via Pi CPU temp as proxy | journald |

---

## Test Scenarios

| Day | Scenario | Expected Status | Pass Criterion |
|-----|----------|----------------|----------------|
| 1 | Normal operation, clean filter | GREEN | ALL_NORMAL for > 90% of minutes |
| 2 | Partially close discharge valve (reduce flow to 60% of normal) | YELLOW FLOW_DECLINING | Status changes within 3 minutes of valve change |
| 3 | Disconnect P1 signal wire (simulate LOOP_LOW_FAULT) | RED SENSOR_FAULT | RED fires within 2 minutes |
| 3 | Reconnect P1 | GREEN | Returns to GREEN within 3 minutes |
| 4 | Close discharge valve fully (no flow, pump on) | RED NO_FLOW_PUMP_ON | RED fires within 2 minutes |
| 4 | Disconnect site Wi-Fi | (network down) | Upload queue builds; reconnect → drains |
| 5 | Hard power cut (pull power) | — | Device restarts, DB intact, heuristics active within 3 min |
| 5 | Restrict filter (partially block) to raise DP | YELLOW/RED HIGH_PRESSURE | Status fires at correct DP threshold |

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| 48-hour continuous run without crash | Required |
| Power cycle test passed | Required (see docs/power_cycle_test_plan.md) |
| AP fallback activates and reverts correctly | Required |
| All test scenario status transitions correct | Required |
| Upload queue drains to 0 within 5 min of reconnect | Required |
| DB integrity_check = ok at end of trial | Required |
| CPU temperature stays below 70°C during peak outdoor temperature | Target |
| SD card shows no filesystem errors in dmesg | Required |

---

## Yard Trial Log

| Date | Scenario | Status Observed | Notes | Tester |
|------|----------|----------------|-------|--------|
| | | | | |
| | | | | |

---

## Go/No-Go at End of Yard Trial

All success criteria must pass before proceeding to field installation.

Gate 2 signoff: docs/phase_gate_signoff.md — complete that form.
