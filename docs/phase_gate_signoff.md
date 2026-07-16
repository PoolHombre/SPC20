# Phase Gate Signoff — SPC 2.0 Build 1

Each gate must be fully signed off before proceeding to the next phase.
All rows must show Pass. A single Fail or blank blocks the gate.

---

## Gate 1 — Bench Gate Signoff

**Purpose:** Confirm the device hardware and software work correctly in a controlled lab environment before yard exposure.

| Item | Pass/Fail | Evidence / Notes | Reviewer | Date |
|------|-----------|-----------------|----------|------|
| Sensor readings verified — all 4 AI channels return expected mA under bench conditions | | Screenshot of /api/status or log excerpt | | |
| Calibration complete — ambient_zero accepted on P1, P2, P3 (stddev < 0.05 mA) | | calibration_events records in local DB | | |
| Heuristics tested — GREEN scenario confirmed in simulator | | pytest test_heuristics.py passing | | |
| Heuristics tested — RED: NO_FLOW_PUMP_ON fires correctly | | Test log or pytest output | | |
| Heuristics tested — RED: LOW_WATER_LOSING_PRIME fires correctly | | Test log or pytest output | | |
| Heuristics tested — YELLOW: FILTER_SERVICE_SOON fires correctly | | Test log or pytest output | | |
| Heuristics tested — pump-off guard: INVALID_PRESSURE_RELATIONSHIP does NOT fire when pump off | | pytest test_heuristics.py passing | | |
| Supabase upload confirmed — at least 5 minutes of readings appear in cloud DB | | Supabase table viewer screenshot | | |
| Local dashboard accessible — /api/status returns 200, no secrets in response | | curl output or browser screenshot | | |
| Auth blocks calibration POST without credentials | | curl -X POST /api/calibration/ambient-zero returns 401 without auth | | |
| Power cycle test passed — DB intact after hard power cut | | integrity_check() returns True after reboot | | |
| Secrets audit passed — SUPABASE_SERVICE_ROLE_KEY not in /etc/spc20/.env | | grep output | | |
| All pytest tests passing | | pytest output, 0 failures | | |
| Local buffer restart survival — data survives simulated reboot | | pytest test_buffer.py passing | | |

**Decision:** Proceed / Hold / Repeat

**Signed by:** _________________________ **Date:** _____________

---

## Gate 2 — Yard Gate Signoff

**Purpose:** Confirm the device survives outdoor conditions, real sensor signals, and extended unattended operation.

| Item | Pass/Fail | Evidence / Notes | Reviewer | Date |
|------|-----------|-----------------|----------|------|
| Outdoor enclosure weatherproofing confirmed — IP67 gasket seated, cable glands tight | | Visual inspection photo | | |
| Cable routing and strain relief verified — no bare conductors, cables secured | | Photo of conduit and glands | | |
| Real sensor readings vs. known values — P1/P2/P3 checked against calibrated gauge | | Gauge photo + log excerpt side-by-side | | |
| Flow transmitter reading vs. known flow rate (bucket test or reference meter) | | Flow log vs. reference measurement | | |
| AP fallback tested — device activates AP when Wi-Fi disconnected | | nmcli output showing AP active | | |
| AP fallback revert — device reconnects to site Wi-Fi when upstream restored | | NM log showing reversion | | |
| 48-hour continuous run — no crashes, no DB corruption | | journalctl and /api/health over 48 hr window | | |
| All alert conditions tested with pool in known states (filter loaded, pump off, etc.) | | Test scenario log | | |
| Supabase upload queue drains after reconnect (no stuck pending rows) | | /api/status upload_queue_depth = 0 after upload | | |
| Network watchdog service enabled and auto-starting | | systemctl is-enabled spc20-network-watchdog | | |
| Log rotation configured — logs not filling SD card | | logrotate config and df output | | |
| OverlayFS or read-only root in place (or confirmed not needed for yard) | | pi_field_hardening.md step completed | | |
| Power cycle test — yard enclosure powered off and on, readings resume within 2 minutes | | Timestamp of first reading after reboot vs. power-on time | | |

**Decision:** Proceed / Hold / Repeat

**Signed by:** _________________________ **Date:** _____________

---

## Gate 3 — Field Gate Signoff

**Purpose:** Confirm the device and site are ready for unattended customer-premises operation.

| Item | Pass/Fail | Evidence / Notes | Reviewer | Date |
|------|-----------|-----------------|----------|------|
| Site survey complete — electrical panel, sensor taps, conduit routing documented | | Site survey form / photos | | |
| Customer sign-off on install location — signed site approval form | | Signed PDF in project folder | | |
| Static IP or DHCP reservation confirmed for device on site LAN | | Router screenshot or IT confirmation email | | |
| Firewall rules confirmed — device can reach Supabase ingest URL on port 443 | | curl test from device: curl -I ${SUPABASE_INGEST_URL} | | |
| SD card endurance config in place — OverlayFS or persistent /var/lib/spc20 partition | | docs/pi_field_hardening.md steps completed | | |
| Watchdog timer enabled (hardware WDT or systemd watchdog) | | systemctl status watchdog | | |
| Emergency contact list — who to call if device goes offline | | Contact list in site folder | | |
| Data retention policy acknowledged by customer — how long raw data is stored | | Signed data agreement or email | | |
| UPS / battery backup installed and tested — device survives 30-min power outage | | UPS test log | | |
| Cable labels — all sensor wires labeled at both ends (P1/P2/P3/FLOW/DI) | | Photo of labeled cables | | |
| Device label visible — DEVICE_ID and AP password printed on enclosure | | Photo of label | | |
| Remote access path confirmed — VPN, Tailscale, or cellular backup tested | | SSH test from off-site | | |
| First-week monitoring plan agreed — daily check-in for 7 days post-install | | Plan documented | | |
| Supabase project configured with correct site_id and device_id | | Database query confirming row | | |

**Decision:** Proceed / Hold / Repeat

**Signed by:** _________________________ **Date:** _____________
