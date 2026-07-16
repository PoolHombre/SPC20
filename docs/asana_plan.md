# SPC 2.0 — Asana Project Plan

**Project:** SPC 2.0 - Read-Only Proof of Concept
**Owner:** Kevin McAuley
**Start:** 2026-07-16
**Target field trial complete:** 2026-10-31

---

## Milestones

| Milestone | Code | Description | Target Date |
|-----------|------|-------------|-------------|
| M1 | SCOPE | Build 1 scope defined and project structure set up | 2026-07-18 |
| M2 | BENCH-HW | Bench hardware assembled and sensor chain verified | 2026-07-25 |
| M3 | BENCH-SW | Software running with simulator; all tests passing | 2026-07-28 |
| M4 | BENCH-GATE | Gate 1 (Bench) signed off — all 14 checklist items pass | 2026-08-01 |
| M5 | HARDEN | Phase 1A field hardening complete (OverlayFS, WDT, SD endurance) | 2026-08-08 |
| M6 | YARD-HW | Yard enclosure built; real sensors installed on pipe rig | 2026-08-15 |
| M7 | YARD-DATA | 5-day yard data trial complete; all scenarios tested | 2026-08-22 |
| M8 | YARD-GATE | Gate 2 (Yard) signed off | 2026-08-25 |
| M9 | FIELD-SURVEY | Field site survey complete; customer sign-off | 2026-09-05 |
| M10 | FIELD-INSTALL | Device installed at field site; first reading in Supabase | 2026-09-12 |
| M11 | FIELD-TRIAL | 14-day field trial complete; dispatch accuracy data collected | 2026-09-30 |
| M12 | BUILD2-DECISION | Build 2 go/no-go decision documented | 2026-10-15 |

---

## Section 0 — SPC 2.0 Build 1 Scope and Management

Tasks: project setup, repository structure, Supabase project creation, coordination.

**M1 target:** 2026-07-18

---

## Section 1 — Build 1A Bench Hardware

Tasks: Pi imaging, HAT installation, loop power supply wiring, 4-20 mA signal injection testing.

**M2 target:** 2026-07-25

---

## Section 2 — Build 1A Bench Software and Supabase

Tasks: Python package structure, sensor adapter, heuristics, Flask dashboard, Supabase migrations, Edge Function deploy.

**M3 target:** 2026-07-28

---

## Section 3 — Build 1A Bench Validation Gate

Tasks: run pytest suite, verify all 14 Gate 1 checklist items, sign off Gate 1.

**M4 target:** 2026-08-01

---

## Section 4 — Phase 1A Field Hardening

Tasks: OverlayFS, persistent data partition, hardware watchdog, SD card upgrade, AP profile, power cycle test.

**M5 target:** 2026-08-08

---

## Section 5 — Build 1B Yard Hardware Conversion

Tasks: outdoor enclosure, DIN rail, terminal blocks, cable glands, real transmitter wiring, grounding checklist.

**M6 target:** 2026-08-15

---

## Section 6 — Build 1B Yard Data Trial

Tasks: 5-day yard trial, all scenario tests, AP fallback test, network reconnect test.

**M7 target:** 2026-08-22

---

## Section 7 — Build 1B Yard Validation Gate

Tasks: Gate 2 checklist, yard trial report, Gate 2 sign-off.

**M8 target:** 2026-08-25

---

## Section 8 — Build 1C Field Site Survey

Tasks: site survey form, customer sign-off on location, network/firewall assessment, UPS sizing.

**M9 target:** 2026-09-05

---

## Section 9 — Build 1C Field Install

Tasks: conduit, tap installation, transmitter calibration, device network config, first reading verified in Supabase, Gate 3 sign-off.

**M10 target:** 2026-09-12

---

## Section 10 — Build 1C Field Trial

Tasks: 14-day monitoring, daily check-ins, weekly dispatch accuracy comparison vs. technician ground truth, upload queue monitoring.

**M11 target:** 2026-09-30

---

## Section 11 — Build 1C Field Review and Build 2 Decision

Tasks: trial report, dispatch accuracy analysis, technician interview, Build 2 decision document, ADR.

**M12 target:** 2026-10-15
