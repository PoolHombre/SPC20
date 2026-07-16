# SPC 2.0 Bench Acceptance Test Plan

Execute this plan on every unit before field deployment. A unit does not ship until all tests PASS.

Equipment required:
- 4-20 mA loop calibrator/simulator (e.g., Fluke 709)
- Digital multimeter
- Laptop with SSH access to the Pi
- Network access (Ethernet to router, or hotspot)
- `.env` file pre-loaded with a valid DEVICE_TOKEN and SUPABASE_INGEST_URL

---

## Test 1: Power-Up and OS Boot

| Field | Detail |
|-------|--------|
| Objective | Confirm the Pi boots cleanly and the OS is stable |
| Procedure | 1. Connect PSU to 120 VAC. Confirm 24 VDC at TB-2- to TB-1+ terminals (DMM). 2. Apply Pi power (USB-C or HAT 5V rail). 3. Wait 60 seconds. 4. SSH into Pi (`ssh pi@<hostname>`). 5. Run `uptime` and `dmesg | tail -20`. |
| Expected | SSH succeeds. No kernel errors in dmesg. Uptime < 5 min confirming fresh boot. |
| Pass / Fail | |
| Notes | |

---

## Test 2: Analog Channel 1 (P1 Suction) — 4 mA (minimum)

| Field | Detail |
|-------|--------|
| Objective | Verify P1 channel reads 4 mA and scales to -15.0 PSI |
| Procedure | 1. Connect loop calibrator to HAT AI-1 in simulate mode. 2. Set output to 4.000 mA. 3. Run `python3 -c "from src.sensors import SimulatorAdapter; ..."` or check raw HAT register via i2cget. 4. Run logger with `LOG_LEVEL=DEBUG` and verify log shows `p1_suction_psi_avg` near -15.0. |
| Expected | Raw mA reading 4.00 ± 0.05. Scaled EU = -15.0 PSI ± 0.1. |
| Pass / Fail | |
| Notes | |

---

## Test 3: Analog Channel 1 (P1) — 12 mA (midpoint)

| Field | Detail |
|-------|--------|
| Objective | Verify midpoint scaling (12 mA = 0.0 PSI for P1) |
| Procedure | Set calibrator to 12.000 mA on AI-1. Read logger output. |
| Expected | Scaled EU = 0.0 PSI ± 0.2 |
| Pass / Fail | |
| Notes | |

---

## Test 4: Analog Channel 1 (P1) — 20 mA (maximum)

| Field | Detail |
|-------|--------|
| Objective | Verify full-scale reading (20 mA = +15.0 PSI) |
| Procedure | Set calibrator to 20.000 mA on AI-1. Read logger output. |
| Expected | Scaled EU = 15.0 PSI ± 0.1 |
| Pass / Fail | |
| Notes | |

---

## Test 5: Analog Channels 2 and 3 (P2, P3) — 4/12/20 mA

| Field | Detail |
|-------|--------|
| Objective | Verify P2 and P3 channels scale correctly (0-100 PSI range) |
| Procedure | Repeat 4/12/20 mA injection on AI-2 and AI-3. |
| Expected | 4 mA = 0.0 PSI, 12 mA = 50.0 PSI, 20 mA = 100.0 PSI (±0.5 PSI) |
| Pass / Fail | |
| Notes | |

---

## Test 6: Analog Channel 4 (Flow) — 4/12/20 mA

| Field | Detail |
|-------|--------|
| Objective | Verify flow channel scales correctly (0-500 GPM) |
| Procedure | Repeat 4/12/20 mA injection on AI-4. |
| Expected | 4 mA = 0 GPM, 12 mA = 250 GPM, 20 mA = 500 GPM (±2 GPM) |
| Pass / Fail | |
| Notes | |

---

## Test 7: Digital Input (Pump Proof) — OFF

| Field | Detail |
|-------|--------|
| Objective | Verify digital input reads LOW (pump off) with open contact |
| Procedure | Ensure DI-1 wires are connected to terminal block but contact switch is open (no current). Check logger output for `pump_running: false`. |
| Expected | `pump_running` = False in logger output |
| Pass / Fail | |
| Notes | |

---

## Test 8: Digital Input (Pump Proof) — ON

| Field | Detail |
|-------|--------|
| Objective | Verify digital input reads HIGH (pump on) with closed contact |
| Procedure | Jumper DI-1 terminals to simulate closed contact. Verify logger output. |
| Expected | `pump_running` = True in logger output |
| Pass / Fail | |
| Notes | |

---

## Test 9: Logger Startup and GREEN Scenario

| Field | Detail |
|-------|--------|
| Objective | Verify end-to-end logger startup, GREEN scenario, and log output format |
| Procedure | 1. Set `SIM_SCENARIO=green SENSOR_ADAPTER=simulator` in environment. 2. Start logger: `python -m src.logger`. 3. Wait 65 seconds for first summary cycle. 4. Inspect log output. |
| Expected | Log line contains `GREEN NO_VISIT` and `ALL_NORMAL`. No exceptions. |
| Pass / Fail | |
| Notes | |

---

## Test 10: Local SQLite Buffer — Network Unavailable

| Field | Detail |
|-------|--------|
| Objective | Confirm telemetry queues locally when the network is unreachable |
| Procedure | 1. Disconnect Ethernet cable or set firewall rule to block outbound to Supabase URL. 2. Run logger for 3 minutes (3 summary cycles). 3. Check SQLite: `sqlite3 spc20_buffer.db "SELECT count(*) FROM telemetry_queue WHERE uploaded=0;"` |
| Expected | Count >= 3 rows with `uploaded=0`. Logger logs "Upload failed — buffered row N" for each cycle. |
| Pass / Fail | |
| Notes | |

---

## Test 11: Upload Retry After Reconnect

| Field | Detail |
|-------|--------|
| Objective | Confirm buffered rows are uploaded when network is restored |
| Procedure | 1. After Test 10, reconnect network. 2. Wait for next summary cycle (up to 60 seconds). 3. Check SQLite: `SELECT count(*) FROM telemetry_queue WHERE uploaded=0;` 4. Check Supabase `readings_1min` table for the device. |
| Expected | Buffered rows marked `uploaded=1`. Rows appear in Supabase. |
| Pass / Fail | |
| Notes | |

---

## Test 12: RED Scenario — Loss of Prime

| Field | Detail |
|-------|--------|
| Objective | Verify RED/SEND_NOW dispatch for loss-of-prime condition |
| Procedure | Set `SIM_SCENARIO=red_loss_of_prime`. Restart logger. Wait 65 seconds. |
| Expected | Log shows `RED SEND_NOW LOW_WATER_LOSING_PRIME` |
| Pass / Fail | |
| Notes | |

---

## Test 13: RED Scenario — No Flow

| Field | Detail |
|-------|--------|
| Objective | Verify RED/SEND_NOW dispatch for no-flow condition |
| Procedure | Set `SIM_SCENARIO=red_no_flow`. Restart logger. Wait 65 seconds. |
| Expected | Log shows `RED SEND_NOW NO_FLOW_PUMP_ON` |
| Pass / Fail | |
| Notes | |

---

## Test 14: YELLOW Scenario — Filter Service

| Field | Detail |
|-------|--------|
| Objective | Verify YELLOW/ROUTE_TODAY dispatch for high filter DP |
| Procedure | Set `SIM_SCENARIO=yellow_filter`. Restart logger. Wait 65 seconds. |
| Expected | Log shows `YELLOW ROUTE_TODAY FILTER_SERVICE_WITHIN_24_HOURS` or `FILTER_LOADING_HIGH` |
| Pass / Fail | |
| Notes | |

---

## Test 15: Sensor Fault Scenario

| Field | Detail |
|-------|--------|
| Objective | Verify RED/SEND_NOW dispatch for under-range sensor fault |
| Procedure | Set `SIM_SCENARIO=fault_under`. Restart logger. Wait 65 seconds. |
| Expected | Log shows `RED SEND_NOW SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION` |
| Pass / Fail | |
| Notes | |

---

## Test 16: Supabase Record Verification

| Field | Detail |
|-------|--------|
| Objective | Confirm GREEN scenario data appears correctly in Supabase |
| Procedure | 1. Run GREEN simulator for 2 minutes. 2. Open Supabase table editor or run: `SELECT * FROM readings_1min WHERE device_id = 'spc20-poc-0001' ORDER BY observed_at DESC LIMIT 5;` 3. Check `route_status_current` for the bench pool. |
| Expected | `readings_1min` has 2+ rows with correct PSI and GPM values. `route_status_current` shows `dispatch_status = 'GREEN'`. |
| Pass / Fail | |
| Notes | |

---

## Test 17: systemd Service Start/Stop/Restart

| Field | Detail |
|-------|--------|
| Objective | Verify the systemd service manages the logger correctly |
| Procedure | 1. `sudo systemctl start spc20-logger`. 2. `sudo systemctl status spc20-logger` — verify Active: running. 3. `sudo systemctl stop spc20-logger`. 4. Verify process stops. 5. Kill the logger process manually while running, verify it restarts automatically within 10 seconds. |
| Expected | Service starts and stops cleanly. Auto-restarts after kill. Logs appear in `journalctl -u spc20-logger`. |
| Pass / Fail | |
| Notes | |

---

## Sign-Off

| Field | |
|-------|-|
| Unit serial / device_id | |
| Tested by | |
| Date | |
| Overall result | PASS / FAIL |
| Outstanding issues | |
