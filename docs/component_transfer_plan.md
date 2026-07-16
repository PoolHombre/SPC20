# Component Transfer Plan — Bench → Yard → Field

## Purpose

Track what carries forward unchanged between phases, what needs adaptation, and what is rebuilt per-site. This prevents assumptions that bench-tested components "just work" in the field.

---

## Reusability Matrix

| Component | Bench → Yard | Yard → Field | Notes |
|-----------|-------------|-------------|-------|
| Raspberry Pi 4B | Transfers as-is | Transfers as-is | Same unit, same SD |
| Sequent HAT | Transfers as-is | Transfers as-is | No config changes |
| Python package (src/spc20) | Transfers as-is | Transfers as-is | Config via .env |
| systemd services | Transfers as-is | Transfers as-is | Same unit files |
| SQLite DB | Fresh at each phase | Fresh at each phase | New trial_run_id each phase |
| .env configuration | New values for yard | New values per site | DEVICE_ID, SITE_ID, network |
| Supabase project | Same project | Same project | New trial_run row |
| Pressure transmitters | Same transmitters | Re-calibrated on site | Calibration not portable |
| Flow transmitter | Same transmitter | Re-calibrated on site | Full-scale depends on pipe size |
| Sensor wiring | Rebuilt for outdoor enclosure | Rebuilt at site | Cable lengths change |
| Outdoor enclosure | New for yard | Transfers to field | IP67 enclosure stays |
| 24V loop PSU | New for yard | Transfers to field | Sized for 4 loops |
| UPS / battery | New for field | N/A | Not needed at yard |
| AP NetworkManager profile | Tested at bench | Updated SSID for field unit | Per-device SSID |
| Site Wi-Fi NM profile | N/A | New per site | Yard uses own network |
| OverlayFS / partition | Configured at yard stage | Transfers | SD endurance |
| Log rotation config | Configured at yard | Transfers | |
| Hardware watchdog | Configured at yard | Transfers | dtparam=watchdog=on |

---

## What Must Be Rebuilt Per Site

- `/etc/spc20/.env` — site-specific values: SITE_ID, Wi-Fi credentials, DEVICE_TOKEN (if per-site)
- NetworkManager site-wifi profile — per-site SSID and password
- Calibration events — ambient_zero and static_baseline must be run at each site (pressure taps have different static head)
- `trial_runs` row in Supabase — new TRIAL_RUN_ID per site per phase
- Wiring — cable lengths, conduit, terminal block labeling — all site-specific
- Sensor tap locations — drilled and tapped per system layout

---

## What Never Changes

- Source code (unless a bug is found or a feature added) — version-pinned via git tag
- Supabase schema — same migrations applied to all
- Dispatch heuristic thresholds — configurable per site via .env, but same logic
- Security model — SUPABASE_SERVICE_ROLE_KEY never on device, regardless of site

---

## Known Risks at Transition

| Transition | Risk | Mitigation |
|------------|------|------------|
| Bench → Yard | Outdoor temperature affects mA baseline | Re-run ambient_zero in yard environment |
| Bench → Yard | Real sensor noise higher than simulator | Verify calibration_stddev_limit is appropriate; increase if needed |
| Yard → Field | Site pipe size changes flow transmitter full-scale | Re-configure FLOW_MAX_GPM and re-calibrate |
| Yard → Field | Site power quality (surges, brownouts) | UPS required for field; tested at yard gate |
| Any | Supabase migration not applied | Apply and verify before first reading |
