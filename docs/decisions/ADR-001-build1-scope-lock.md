# ADR-001: Build 1 Scope Lock — Read-Only Monitoring Only

**Status:** Accepted
**Date:** 2026-07-16
**Deciders:** Kevin McAuley
**Applies to:** SPC 2.0 Build 1 (1A Bench, 1B Yard, 1C Field) and Phase 1A Field Hardening

## Context

SPC 2.0 is a proof-of-concept IoT monitor for commercial swimming-pool circulation
and filtration systems. Its purpose in Build 1 is to answer three dispatch questions
remotely — do we need to visit, how urgently, and what should the technician check
first — expressed as GREEN (no visit), YELLOW (route today), RED (send now).

A POC that both monitors and controls equipment would multiply hardware cost,
liability exposure, certification scope, and failure modes before the core
hypothesis — that sensor-derived dispatch status is accurate and useful for route
optimization — has been validated. Every additional capability also delays the
staged Bench → Yard → Field trial sequence.

## Decision

Build 1 is **strictly read-only**. The device observes and classifies; it never
actuates. The following are explicitly **out of scope** for all of Build 1:

| Excluded capability | Rationale |
|---|---|
| Pump control / shutdown | Liability and safety scope; requires certification and interlock design |
| Cloud-to-device command/control | No actuation means no command path is needed; reduces attack surface |
| BLE technician app | Local Flask dashboard over LAN/AP covers the technician use case |
| RS-485 / Modbus integration | Off-the-shelf 4–20 mA covers all Build 1 sensors |
| Custom PCB | Raspberry Pi + industrial HAT is sufficient for trial volumes |
| Mobile app | Browser dashboard is adequate for POC |
| Production enclosure certification | NEMA 4X off-the-shelf enclosure is sufficient for trials |
| Automated customer billing / dispatch integration | Dispatch status is consumed by humans in Build 1 |

The read-only rule extends to installation practice: the logger must never be
inserted into an existing control or safety loop. Shared 4–20 mA signals are taken
through splitters/isolators only (see `docs/grounding_and_isolation_checklist.md`).

## Consequences

- Hardware BOM stays off-the-shelf (~$700/unit core) and transfers Bench → Yard → Field.
- The Supabase ingest path is one-directional: device → cloud. No device-command
  tables, topics, or endpoints exist, and none should be added in Build 1.
- Any capability listed above requires a new ADR and a Build 2 decision before
  implementation. The Build 2 go/no-go gate (M12) is the earliest point at which
  this scope may be revisited.
- If a trial reveals a condition where automatic pump shutdown would have prevented
  equipment damage, that is **evidence for the Build 2 case**, not grounds to add
  control mid-trial. Document it in the trial log.

## Related

- `docs/build1_phase_gates.md` — gate criteria enforcing this scope at each phase
- `docs/phase_gate_signoff.md` — signoff checklists
- GitHub issue #9 — scope lock task (M1)
