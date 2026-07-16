# SPC 2.0 — Asana Project Plan

**Project:** SPC 2.0 - Read-Only Proof of Concept  
**Owner:** Kevin McAuley  
**Start:** 2026-07-16  
**Target pilot complete:** 2026-09-30

---

## Milestones

| ID | Milestone | Target Date |
|----|-----------|-------------|
| M1 | Hardware purchased and on hand | 2026-07-30 |
| M2 | Bench acceptance test PASS (all 17 tests) | 2026-08-13 |
| M3 | Supabase backend live and accepting data | 2026-08-13 |
| M4 | Pilot site selected and survey complete | 2026-08-20 |
| M5 | Field installation complete and 24-hour soak passed | 2026-08-27 |
| M6 | 14-day trial complete | 2026-09-10 |
| M7 | Pilot report published | 2026-09-17 |
| M8 | Fleet deployment decision | 2026-09-30 |

---

## Section 1: Project Setup

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Create Asana project and import task list | All tasks visible in Asana with correct sections and priorities | None | 0.5h | Kevin |
| Create GitHub repo (SPC20) and push scaffold | Repo live at github.com/PoolHombre/SPC20, all scaffold files committed | None | 0.5h | Kevin |
| Create Supabase project | Supabase project exists, URL and service role key saved | None | 0.5h | Kevin |
| Set up .env.example and document secrets process | .env.example committed, instructions for local setup in README | Supabase project | 0.5h | Kevin |
| Write README.md | README covers purpose, quickstart, simulator usage, and architecture overview | Scaffold complete | 1h | Kevin |

---

## Section 2: Hardware Procurement (M1)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Order Raspberry Pi 4B 4GB | Unit received and confirmed bootable | None | 0.5h | Kevin |
| Order Sequent Microsystems Industrial HAT | HAT received, HAT mounts on Pi | Pi received | 0.5h | Kevin |
| Order Mean Well HDR-60-24 PSU | PSU received, 24 VDC verified at output terminals | None | 0.5h | Kevin |
| Order NEMA 4X enclosure | Enclosure received, DIN components fit inside | HAT received (measure stack height first) | 0.5h | Kevin |
| Order pressure transmitters (P1 compound, P2/P3 gauge) | All 3 transmitters received, NPT threads verified | None | 0.5h | Kevin |
| Order flow transmitter (clamp-on or insertion) | Transmitter received, model confirmed for site pipe | Site survey complete | 1h | Kevin |
| Order clamp-on current switch | Switch received, jaw size confirmed for motor cable | Site survey complete | 0.5h | Kevin |
| Order DIN rail, terminal blocks, fuse block, cable glands | All panel components received | None | 0.5h | Kevin |
| Order SanDisk MAX Endurance 64GB microSD | Card received | None | 0.5h | Kevin |
| Order 4-20mA loop calibrator (or confirm rental) | Calibrator available for bench test date | None | 0.5h | Kevin |
| **MILESTONE M1: All hardware on hand** | All items checked off above | All procurement tasks | — | Kevin |

---

## Section 3: Software and Backend (M3)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Apply Supabase migration (20260716000001_spc20_initial.sql) | All tables created, seed device and pool rows present | Supabase project | 0.5h | Kevin |
| Deploy spc20-ingest Edge Function | Function deployed and returns 200 on test POST with valid device token | Migration applied | 1h | Kevin |
| Verify token hash workflow end-to-end | POST with correct token → 200; wrong token → 403 | Edge function deployed | 0.5h | Kevin |
| Set device_configs defaults for bench pool | device_configs row exists with appropriate thresholds for bench test | Migration applied | 0.5h | Kevin |
| Install Raspberry Pi OS Lite on microSD | Pi boots to CLI, SSH works, hostname set | Pi and microSD received | 1h | Kevin |
| Install Python 3.11+ and project dependencies on Pi | `python --version` >= 3.11; `pip install -e .` succeeds | Pi OS installed | 1h | Kevin |
| Deploy spc20-logger systemd service to Pi | `systemctl status spc20-logger` shows active; GREEN log appears after 60 seconds in simulator mode | Dependencies installed | 1h | Kevin |
| Confirm simulator → Supabase pipeline works | readings_1min receives data from Pi; route_status_current updates | Service deployed | 0.5h | Kevin |
| **MILESTONE M3: Backend live and accepting data** | readings_1min shows continuous GREEN data from bench device | All software tasks | — | Kevin |

---

## Section 4: Bench Hardware Assembly

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Mount DIN rail components in enclosure | PSU, fuse block, terminal blocks mounted and labeled | All hardware received | 2h | Kevin |
| Wire power distribution (PSU → fuse block → common bus) | 24 VDC present at all fused outputs | DIN components mounted | 1h | Kevin |
| Wire HAT to Pi and confirm HAT firmware version | HAT seated on Pi GPIO; i2c device visible (`i2cdetect -y 1`) | HAT and Pi received | 1h | Kevin |
| Wire simulated 4-20mA loops for bench test | Calibrator can source current into HAT inputs; logger reads it | Wiring complete | 1h | Kevin |
| Wire digital input for pump proof simulation | Jumper can simulate DI-1 HIGH/LOW; logger reflects pump_running state | Wiring complete | 0.5h | Kevin |

---

## Section 5: Bench Acceptance Test (M2)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Execute bench test plan Tests 1–8 (power, analog, digital) | All PASS | Bench hardware assembled; calibrator available | 3h | Kevin |
| Execute bench test plan Tests 9–11 (logger, buffer, retry) | All PASS | Tests 1–8 PASS | 2h | Kevin |
| Execute bench test plan Tests 12–15 (scenario tests) | All PASS | Tests 9–11 PASS | 1h | Kevin |
| Execute bench test plan Tests 16–17 (Supabase, systemd) | All PASS | Tests 12–15 PASS; Backend live | 1h | Kevin |
| Document any failures and rework | All failures resolved and re-tested | Full test run | TBD | Kevin |
| **MILESTONE M2: Bench acceptance test PASS** | Bench test plan signed off, all 17 tests PASS | All bench test tasks | — | Kevin |

---

## Section 6: Site Survey and Pilot Site Selection (M4)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Identify candidate pilot pools (min 3) | List of 3 candidate pools with known visit history and recent service events | None | 1h | Kevin |
| Complete site survey checklist for top candidate | All fields in field_install_checklist.md Section 1 complete | Candidate identified | 2h | Kevin |
| Confirm flow transmitter model for pilot site pipe | Transmitter on hand matches pipe size/material | Site survey | 1h | Kevin |
| Configure device_configs for pilot site thresholds | required_flow_gpm, P2/P3 ranges updated for site | Site survey | 0.5h | Kevin |
| Brief site owner | Site owner confirms they understand read-only nature; emergency contact exchanged | Site selected | 0.5h | Kevin |
| Identify technician observer for trial | Technician confirmed and briefed on daily observation form | Site selected | 0.5h | Kevin |
| **MILESTONE M4: Pilot site ready** | Survey complete, technician briefed, configs updated | All survey tasks | — | Kevin |

---

## Section 7: Field Installation (M5)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Install enclosure at pilot site | Enclosure mounted, cable glands fitted | M2, M4 | 1h | Kevin |
| Install P1 transmitter (suction) | Transmitter installed, no leaks, signal wire run to enclosure | Enclosure mounted | 0.5h | Kevin |
| Install P2 transmitter (filter inlet) | As above | Enclosure mounted | 0.5h | Kevin |
| Install P3 transmitter (filter outlet) | As above | Enclosure mounted | 0.5h | Kevin |
| Install flow transmitter | Transmitter installed per manufacturer spec, cable run to enclosure | Enclosure mounted | 1h | Kevin |
| Install current switch on pump motor | Switch clamped, trip point set, DI-1 wired | Enclosure mounted | 0.5h | Kevin |
| Wire all terminal blocks per wiring diagram | All terminals labeled, wiring photo taken | All sensors installed | 1h | Kevin |
| Configure Pi WiFi for site network | Pi connects to site WiFi; ping Supabase URL succeeds | Pi on site | 0.5h | Kevin |
| Power up and run field verification checks | All checks in field_install_checklist.md Section 4 pass | All wiring done | 1h | Kevin |
| 24-hour soak | readings_1min has data with no gaps >5 min; GREEN status expected | Field verification pass | 24h | Kevin |
| **MILESTONE M5: Field installation complete** | Soak passed, all checklist items signed off | All installation tasks | — | Kevin |

---

## Section 8: 14-Day Trial (M6)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Days 1–3: Baseline data collection (no threshold changes) | 3 full days of continuous data; technician observation form completed each day | M5 | — | Kevin + Tech |
| Days 1–3: Review flow and DP distributions | normal_flow band and filter_clean_dp identified for this site | Day 3 data | 1h | Kevin |
| Tune thresholds if needed (Day 3–4) | Thresholds updated in device_configs; changes logged | Day 1–3 review | 1h | Kevin |
| Days 4–14: Daily remote data review | No unexplained gaps; status distribution reviewed | Thresholds set | Daily 0.5h | Kevin |
| Log every RED/YELLOW alert with technician correlation | False-positive/negative log maintained | All days | — | Kevin + Tech |
| On any RED alert: technician visit within 4 hours and observation recorded | Observation form completed for every RED | Any RED | — | Tech |
| **MILESTONE M6: 14-day trial complete** | 14 days of data, all technician forms completed | Trial running | — | Kevin |

---

## Section 9: Pilot Report and Analysis (M7)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Calculate data completeness | % completeness computed from readings_1min gaps | M6 | 1h | Kevin |
| Compile TP/TN/FP/FN table from observation forms | All correlated events classified | M6 | 2h | Kevin |
| Document threshold tuning log | All changes recorded with before/after values and rationale | M6 | 0.5h | Kevin |
| Write pilot report per template outline (trial_plan.md) | Report covers all 8 template sections | Analysis complete | 3h | Kevin |
| Identify recommended heuristic/threshold changes | Specific code or config changes proposed with evidence | Report drafted | 1h | Kevin |
| Publish report to team | Report shared with Poolsure leadership | Report complete | 0.5h | Kevin |
| **MILESTONE M7: Pilot report published** | Report distributed | All analysis tasks | — | Kevin |

---

## Section 10: Fleet Deployment Decision (M8)

| Task | Acceptance Criteria | Dependencies | Effort | Owner Role |
|------|--------------------|----|--------|-----------|
| Review pilot report against exit criteria | Exit criteria documented in trial_plan.md evaluated explicitly | M7 | 1h | Kevin |
| Estimate fleet unit cost for 10/25/50 pools | Cost model produced with hardware + Supabase at each scale | M7 | 2h | Kevin |
| Identify top 10 candidate pools for Phase 2 | Pools ranked by ROI potential (visit frequency, problem history) | M7 | 1h | Kevin |
| Draft Phase 2 proposal (scope, cost, timeline) | Document ready for leadership review | Cost model + pool list | 2h | Kevin |
| Leadership decision: proceed / hold / pivot | Decision recorded with conditions | Phase 2 proposal | — | Leadership |
| **MILESTONE M8: Fleet deployment decision made** | Go/No-Go decision documented | All M8 tasks | — | Leadership |

---

## Priority Key

- **P0** — Blocks a milestone; must not slip
- **P1** — Important; schedule impact if slipped
- **P2** — Nice to have; defer if needed
