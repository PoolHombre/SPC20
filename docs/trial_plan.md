# SPC 2.0 — Build 1 Trial Plan (All Phases)

## Overview

Build 1 consists of three sequential trial phases. Each phase has a gate — all gate criteria must pass before advancing. The device and software carry forward across phases; only the environment and configuration change.

The trials are read-only observation only. The system never controls equipment. Dispatch decisions during trials are advisory and logged for comparison against technician judgment.

---

## Phase 1A — Bench Trial

**Environment:** Dev desk / lab bench with bench power supply, Sequent HAT, and 4-20 mA signal generator or simulator.

**Duration:** 3–5 days of software development and validation.

**Goals:**
- Verify sensor chain (scaling, quality classification, aggregation) with injected signals.
- Verify all heuristic reason codes fire correctly.
- Verify Supabase upload pipeline end-to-end.
- Verify local dashboard renders without secrets in response.
- Verify power cycle survival with SQLite WAL.
- Verify calibration modes (ambient_zero, static_baseline) store correct offsets.
- Run complete pytest suite with 0 failures.

**Success Criteria:**
- All items in Gate 1 (docs/phase_gate_signoff.md) pass.
- Bench phase trial_run row in Supabase.
- At least 30 minutes of GREEN readings in cloud DB.

---

## Phase 1B — Yard Trial

**Environment:** Poolsure yard facility. Controlled pipe and pump rig outdoors. Real sensors, real pump, real filter.

**Duration:** 5–10 days minimum.

**Goals:**
- Validate sensor readings against known-good reference instruments.
- Validate heuristics against real hydraulic events (valve closures, filter restriction).
- Validate outdoor enclosure weatherproofing and thermal performance.
- Validate AP fallback and network watchdog.
- Validate 48-hour unattended operation.
- Validate power cycle recovery.

**Success Criteria:**
- All items in Gate 2 (docs/phase_gate_signoff.md) pass.
- See docs/yard_trial_plan.md for detailed test scenarios and pass criteria.

---

## Phase 1C — Field Trial

**Environment:** Customer commercial pool site. Real pool, real pump room, real customer.

**Duration:** 14 days minimum.

**Goals:**
- Validate dispatch accuracy against technician ground truth (weekly comparison).
- Validate remote monitoring (Tailscale / VPN access for daily check-ins).
- Validate data continuity over real-world network conditions.
- Validate UPS performance through power events.
- Collect data to inform Build 2 feature decisions.

**Data collection:**
- All readings to Supabase (continuous).
- Technician ground truth log: what the technician actually found on each visit.
- Weekly comparison: was SPC 2.0 dispatch_status correct for each visit?

**Success Criteria:**

| Criterion | Target |
|-----------|--------|
| 14-day continuous data | < 5% gap (< 1 hour/day) |
| No unplanned device offline events > 10 min | 0 |
| Dispatch accuracy (vs. technician ground truth) | > 85% agreement |
| No false RED alarms (RED when technician found GREEN) | < 2 per 14 days |
| No missed RED alarms (GREEN when technician found RED/emergency) | 0 |
| Customer satisfaction (qualitative) | Positive feedback from site manager |

**Gate 3 signoff:** docs/phase_gate_signoff.md.

---

## Build 2 Decision

At the end of Phase 1C, the team reviews:
1. Dispatch accuracy data
2. Technician adoption feedback
3. Known issues and bug log
4. Cost per device vs. value generated

Decision options:
- Proceed to Build 2 (feature expansion, fleet deployment)
- Repeat 1C with improvements
- Hold pending further stakeholder review

The decision is documented in a post-trial report and ADR.
