# Build 1 Phase Gates — Measurable Pass Criteria

---

## Gate 1 — Bench (1A)

| Criterion | Measurement | Pass Standard |
|-----------|-------------|---------------|
| Sensor chain functional | All 4 AI channels read mA at known signal level | Each channel within ±0.1 mA of injected signal |
| Quality classifier | Inject 2.0, 3.7, 4.0, 12.0, 20.5, 22.0 mA signals | Correct QualityState returned for each |
| Scaling accuracy | Inject 4, 12, 20 mA; compare EU output | Within ±0.5% of span |
| Calibration — ambient_zero | Run with isolated transmitter | Offset accepted, stddev < 0.05 mA |
| Heuristics — GREEN | Simulator green scenario | GREEN, ALL_NORMAL, confidence = 1.0 |
| Heuristics — RED conditions | Simulator red_no_flow, red_loss_of_prime, fault_over | Correct reason code for each |
| Heuristics — pump-off guard | P3 >= P2 with pump_running=False | No INVALID_PRESSURE_RELATIONSHIP fired |
| Heuristics — YELLOW | Simulator yellow_filter | FILTER_SERVICE_SOON or FILTER_LOADING_HIGH |
| Supabase upload | Run for 5 minutes | >= 5 rows in readings_1min in cloud |
| Local buffer | Power-cut simulation (kill -9) | DB integrity_check = ok on restart |
| Dashboard auth | curl without credentials to /api/calibration/* | 401 returned |
| Secrets audit | grep -r SERVICE_ROLE /etc/spc20/ | 0 matches |
| pytest suite | pytest tests/ -v | 0 failures, 0 errors |

---

## Gate 2 — Yard (1B)

| Criterion | Measurement | Pass Standard |
|-----------|-------------|---------------|
| Enclosure seal | Visual + IP67 submersion test (or equivalent) | No moisture ingress after 30 min at 30 cm |
| Real sensor readings | Compare P2 with calibrated gauge at known pressure | Within ±1 PSI across 0–60 PSI range |
| Real flow readings | Compare flow transmitter to reference (bucket or meter) | Within ±5% of reference |
| 48-hour unattended run | journalctl + /api/health at 48 hr | 0 crashes, DB integrity ok, pending queue = 0 |
| AP fallback activation | Disconnect site Wi-Fi from router | AP SSID appears within 2 minutes |
| AP fallback revert | Reconnect site Wi-Fi | Device reconnects to site within 2 minutes, AP disappears |
| All alert conditions | Manually restrict filter, close valve, etc. | Correct status fired within 2 minutes of condition |
| Log rotation | Check disk usage after 48 hr | /var/log usage < 200 MB |
| OverlayFS or partition | Reboot after write to /var/lib/spc20 | Data persists; no SD wear on /var |
| Power cycle | Hard power cut + restore | First reading within 2 minutes, DB intact |

---

## Gate 3 — Field (1C)

| Criterion | Measurement | Pass Standard |
|-----------|-------------|---------------|
| Site survey complete | Survey form signed | All sections complete |
| Network connectivity | curl -I ${SUPABASE_INGEST_URL} from device | 200 or 401 (not timeout) |
| Static IP / DHCP reservation | Router config screenshot | Device always gets same IP |
| UPS runtime | Kill mains power, measure time until device dies | >= 30 minutes |
| SD endurance config | cat /proc/mounts; verify /var/lib/spc20 on separate partition or OverlayFS active | Confirmed |
| Watchdog timer | Trigger a hang (run test script); verify reboot | Device reboots within 15 seconds |
| Customer sign-off | Signed form | Countersigned by site manager |
| 7-day monitoring | Daily /api/status checks | 0 unplanned offline events > 10 minutes |
| Data in Supabase | Query readings_1min WHERE site_id = '<site>' | >= 7 days of continuous rows (gaps < 5 min) |
