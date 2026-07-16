# Field Alpha Readiness Checklist — SPC 2.0 Build 1C

This checklist must be fully complete before any device is installed at a customer premises.
All items must show DONE. A single OPEN or BLOCKED item is a hold.

---

## Hardware

- [ ] Raspberry Pi 4B (4 GB) procured and imaged
- [ ] Sequent Microsystems Industrial Automation HAT installed and tested
- [ ] All 4 pressure transmitters (4-20 mA, 2-wire) calibrated and verified
- [ ] Flow transmitter (4-20 mA) calibrated and verified
- [ ] Pump DI wiring confirmed (dry contact, not live)
- [ ] IP67 or better outdoor enclosure with sealed cable glands
- [ ] 24 VDC loop power supply in enclosure with fusing
- [ ] DIN rail and terminal blocks installed
- [ ] Industrial-grade SD card (pSLC or equivalent) installed
- [ ] UPS / battery backup installed and tested (min 30 min runtime)
- [ ] All wiring labeled at both ends (P1/P2/P3/FLOW/PUMP/24V/GND)
- [ ] Enclosure grounded to panel chassis ground
- [ ] Device label printed and affixed (DEVICE_ID, AP SSID, AP password prefix)

## Software

- [ ] Raspberry Pi OS Bookworm Lite (64-bit) installed
- [ ] NetworkManager confirmed managing wlan0
- [ ] spc20 Python package installed in venv at /opt/spc20
- [ ] /etc/spc20/.env configured — DEVICE_ID, DEVICE_TOKEN, SUPABASE_INGEST_URL, SENSOR_ADAPTER=sequent
- [ ] SUPABASE_SERVICE_ROLE_KEY confirmed absent from /etc/spc20/.env
- [ ] spc20-logger.service enabled and auto-starting
- [ ] Flask dashboard accessible on port 8080
- [ ] Local AP profile (spc20-ap) created in NetworkManager
- [ ] spc20-network-watchdog.service enabled (if Build 1B target is met)
- [ ] OverlayFS or persistent /var/lib/spc20 partition configured (docs/pi_field_hardening.md)
- [ ] Log rotation configured (logrotate or journald limits)
- [ ] Hardware watchdog timer enabled (dtparam=watchdog=on in config.txt)

## Supabase / Cloud

- [ ] Supabase project created with correct region
- [ ] All migrations applied (20260716000001 and 20260716000002)
- [ ] Edge Function deployed and tested (curl test from device)
- [ ] Device row inserted in devices table (device_id + token hash)
- [ ] trial_runs row created for this field deployment (trial_phase=FIELD, site_id set)
- [ ] Supabase dashboard showing live readings for this device_id

## Documentation

- [ ] Site survey form completed and filed
- [ ] Wiring diagram updated for this site (docs/wiring_diagram.md or site-specific copy)
- [ ] Phase Gate 3 signoff complete (docs/phase_gate_signoff.md)
- [ ] Emergency contact list filed (who to call if device goes offline)
- [ ] Data retention policy acknowledged by customer (signed)
- [ ] DEPLOYMENT_STEPS.md followed and any deviations noted

## Validation Tests

- [ ] Bench Gate (Gate 1) fully signed off
- [ ] Yard Gate (Gate 2) fully signed off
- [ ] Power cycle test passed on actual field hardware
- [ ] 48-hour unattended run in yard environment passed
- [ ] AP fallback tested and reverting correctly
- [ ] Supabase upload queue drains within 5 minutes of connectivity

## Customer Site

- [ ] Customer sign-off on install location (signed form)
- [ ] Static IP or DHCP reservation confirmed on site LAN
- [ ] Firewall allows outbound HTTPS (443) to Supabase
- [ ] Conduit and cable routing approved by site manager
- [ ] Sensor tap locations marked and approved
- [ ] First-week check-in schedule agreed with customer

---

**Field Alpha Go/No-Go Decision:**

Approved to proceed: YES / NO

Signed: _________________________ Date: _____________

Notes:
