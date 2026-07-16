# Local Tech Dashboard — SPC 2.0

The dashboard is a Flask web application running on the device at port 8080. It provides read-only visibility into the device's current state.

---

## Accessing the Dashboard

| Environment | URL |
|-------------|-----|
| Same network as device | `http://<device-ip>:8080` |
| Via AP fallback | `http://192.168.99.1:8080` |
| Via SSH tunnel | `ssh -L 8080:localhost:8080 pi@<device-ip>` then `http://localhost:8080` |

---

## Endpoints

| Endpoint | Auth Required | Purpose |
|----------|--------------|---------|
| `GET /` | No | HTML dashboard (auto-refresh) |
| `GET /api/status` | No | Full JSON status payload |
| `GET /api/live` | No | Minimal live data for polling |
| `GET /api/health` | No | DB integrity and uptime |
| `POST /api/calibration/ambient-zero` | Yes | Queue an ambient_zero calibration |
| `POST /api/calibration/static-baseline` | Yes | Queue a static_baseline calibration |

---

## /api/status Fields Explained

```json
{
  "device_id": "spc20-b1-bench-0001",
  "software_version": "0.1.0",
  "trial_phase": "BENCH",
  "trial_run_id": "bench-run-001",
  "local_time": "2026-07-16T10:30:00+00:00",
  "uptime_seconds": 3600.5,
  "upload_queue_depth": 2,
  "last_upload_time": "2026-07-16T10:29:00+00:00",
  "db_path": "/var/lib/spc20/spc20.db",
  "db_integrity_ok": true,
  "dispatch": {
    "status": "GREEN",
    "action": "NO_VISIT",
    "reason": "ALL_NORMAL",
    "summary": "Flow, pressure, and filter are within normal parameters.",
    "confidence": 1.0,
    "recommended_first_checks": []
  },
  "sensors": {
    "pump_running": true,
    "p1_suction_psi": -2.3,
    "p2_filter_inlet_psi": 18.5,
    "p3_filter_outlet_psi": 12.1,
    "filter_dp_psi": 6.4,
    "flow_gpm": 330.0,
    "raw_ma": {"p1_avg": 7.5, "p2_avg": 9.1, "p3_avg": 7.8, "flow_avg": 12.6},
    "quality": {"p1": "GOOD", "p2": "GOOD", "p3": "GOOD", "flow": "GOOD"}
  }
}
```

| Field | Meaning |
|-------|---------|
| `dispatch.status` | GREEN / YELLOW / RED — the routing recommendation |
| `dispatch.action` | NO_VISIT / ROUTE_TODAY / SEND_NOW |
| `dispatch.reason` | Machine-readable reason code — see docs/heuristics.md |
| `dispatch.confidence` | 0.0–1.0; all automated rules are 0.90–1.0 |
| `dispatch.recommended_first_checks` | What the technician should check first |
| `sensors.filter_dp_psi` | P2 − P3. The primary filter-loading indicator. Clean = ~5 PSI; service = 12 PSI; hard limit = 18 PSI |
| `sensors.p1_suction_psi` | Suction-side pressure. Negative = vacuum/suction. Approaching 0 or oscillating = loss of prime |
| `upload_queue_depth` | Rows pending upload to Supabase. Should drain to 0 when connected |
| `db_integrity_ok` | False = database corruption — do not ignore |
| `quality.*` | GOOD / UNDER_RANGE_WARNING / OVER_RANGE_WARNING / LOOP_LOW_FAULT / LOOP_HIGH_FAULT |

---

## How to Trigger Calibration

Calibration endpoints are protected by HTTP Basic Auth. Default credentials are set in `.env` via `DASHBOARD_PASSWORD_HASH`.

### Ambient Zero (Mode A)

```bash
curl -u tech:<password> -X POST http://<device-ip>:8080/api/calibration/ambient-zero \
  -H "Content-Type: application/json" \
  -d '{"channel": "p1", "notes": "transmitter vented to atmosphere"}'
```

The logger service performs the actual sampling on its next calibration cycle. The endpoint returns an `accepted` acknowledgement — not a completed result.

### Static Baseline (Mode B)

```bash
curl -u tech:<password> -X POST http://<device-ip>:8080/api/calibration/static-baseline \
  -H "Content-Type: application/json" \
  -d '{"notes": "pump confirmed off, system at rest"}'
```

Returns `rejected` (409) if pump_running is True.

---

## Dashboard Indicators at a Glance

| What you see | What it means |
|--------------|---------------|
| GREEN badge | Normal operation — no action |
| YELLOW badge | Needs attention today — include in route |
| RED badge | Send someone now — do not wait for next route |
| upload_queue_depth > 10 | Network issue — readings are buffering locally |
| db_integrity_ok = false | SD card or filesystem problem — replace SD and restore backup |
| quality = LOOP_LOW_FAULT | Open circuit or dead transmitter on that channel |
| quality = LOOP_HIGH_FAULT | Shorted loop on that channel |
| p1_suction_psi pulsing (large stddev) | Loss of prime / cavitation — likely water level |
