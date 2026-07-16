# SPC 2.0 System Overview

## Purpose

SPC 2.0 (Smart Pool Circulation) is a read-only IoT monitoring system designed to give Poolsure service technicians a data-driven dispatch signal for each pool on the route. The system answers one question every minute: does this pool need a technician visit today, urgently, or not at all?

The system is deliberately read-only. It observes — it does not control. No relay, no pump switch, no chemical dosing. This constraint eliminates regulatory complexity, liability exposure, and the risk of a software bug stopping a pool pump.

## Architecture

```
Field Hardware                Edge Device              Cloud Backend           Operations
─────────────────             ────────────             ─────────────           ──────────
P1 Suction (4-20mA) ─┐
P2 Filter In (4-20mA)─┤──→  Raspberry Pi 4B     ──→  Supabase Edge      ──→  Route Dashboard
P3 Filter Out (4-20mA)┤      Sequent HAT             Function (Deno)          (future)
Flow (4-20mA)        ─┤      spc20-logger.py         readings_1min
Pump Proof (dry)     ─┘      LocalBuffer (SQLite)     route_status_current
                             heuristics.py             status_events
```

### Data flow

1. The Sequent Microsystems Industrial HAT reads four 4-20 mA current loops at 1 Hz.
2. The Python logger accumulates 60 raw samples, computes per-channel statistics (avg, min, max, stddev), converts mA to engineering units (PSI, GPM), and evaluates the GREEN/YELLOW/RED dispatch status.
3. The one-minute summary is POST'd to a Supabase Edge Function over HTTPS with a device-specific bearer token.
4. If the network is unavailable, the summary is queued in a local SQLite database and retried on the next successful connection.
5. The Edge Function validates the device token, upserts the reading into `readings_1min`, runs the same heuristic logic server-side, and writes the current dispatch status to `route_status_current`.
6. A future route dashboard reads `route_status_current` to show dispatchers a live GREEN/YELLOW/RED board.

## Hardware Stack

| Component | Purpose |
|-----------|---------|
| Raspberry Pi 4B 4GB | Edge compute, WiFi/LTE connectivity |
| Sequent Microsystems Industrial Automation HAT | 4-channel 4-20 mA analog input, digital inputs, DIN-rail compatible |
| Mean Well HDR-60-24 | 24 VDC DIN-rail power supply for sensors and Pi |
| Polycase ZW-233-16 (or similar) NEMA 4X | Weatherproof enclosure for outdoor pad or pump room installation |
| SanDisk MAX Endurance 64 GB | High-endurance microSD for continuous write workload |
| P1: Ashcroft or equivalent, compound -15/+15 PSI | Suction pressure (can read vacuum) |
| P2: 0-100 PSI transmitter | Filter inlet pressure |
| P3: 0-100 PSI transmitter | Filter outlet pressure |
| Clamp-on current switch | Pump proof — detects motor running without wiring to control circuit |

## Software Stack

| Layer | Technology |
|-------|-----------|
| Edge OS | Raspberry Pi OS Lite (64-bit), systemd service |
| Logger | Python 3.11+, httpx, python-dotenv, smbus2 |
| Local buffer | SQLite via stdlib sqlite3 |
| Cloud backend | Supabase (PostgreSQL + Edge Functions on Deno) |
| Auth | Per-device token, SHA-256 hashed at rest |
| Future dashboard | TBD — Supabase Realtime + React or native mobile app |

## GREEN / YELLOW / RED Dispatch Model

The dispatch model is evaluated every minute from the one-minute telemetry summary. Evaluation is ordered: sensor quality first, then physics validity, then flow/pressure thresholds.

### RED — SEND_NOW

Dispatch a technician immediately. Something is actively wrong.

| Reason Code | Condition |
|-------------|-----------|
| `SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION` | Any channel reads below 3.8 mA or above 20.5 mA while pump is running — cannot verify the pool is circulating |
| `INVALID_PRESSURE_RELATIONSHIP` | P3 (filter outlet) >= P2 (filter inlet) — filter is bypassed, plugged, or gauge is wrong |
| `LOW_WATER_LOSING_PRIME` | Flow avg < 20% of required with high stddev — pulsing pattern indicates suction starvation or loss of prime |
| `NO_FLOW_PUMP_ON` | Flow avg < 20% of required, pump confirmed running, no pulse — blocked, closed valve, or dead impeller |

### YELLOW — ROUTE_TODAY

Include this pool in today's route. Not urgent but needs attention.

| Reason Code | Condition |
|-------------|-----------|
| `FILTER_SERVICE_WITHIN_24_HOURS` | Filter DP >= 12 PSI (service threshold) — backwash or cartridge clean needed |
| `FILTER_LOADING_HIGH` | Filter DP >= 7.5 PSI (1.5x clean threshold) — elevated, monitor closely |
| `FLOW_TREND_DECLINING` | Flow avg below 280 GPM (normal minimum) but above RED threshold |

### GREEN — NO_VISIT

Pool is circulating normally. Skip unless other reasons to visit.

All channels GOOD, P3 < P2, flow within normal band (280–380 GPM by default), filter DP below 7.5 PSI.

## Configuration and Thresholds

All thresholds are configurable per device in the `device_configs` table and mirrored as Python dataclass fields in `src/config.py`. The defaults reflect a typical 50,000-gallon commercial pool. They must be tuned per site during commissioning.

Key parameters:
- `required_flow_gpm`: Design flow rate for this pool. Drives all RED/YELLOW flow calculations.
- `filter_service_dp_psi`: DP at which the filter must be serviced. Default 12 PSI.
- `filter_clean_dp_psi`: DP of a clean filter. Default 5 PSI. YELLOW triggers at 1.5x this value.
- `low_flow_red_threshold_percent`: Flow must drop below this percentage of required before RED triggers. Default 20%.

## Security Model

- Each device has a unique token stored only as a SHA-256 hash in the database.
- Communication is HTTPS only (Supabase enforces TLS).
- The Edge Function validates the token on every request before touching any data.
- The Pi has no inbound ports open. It is outbound-only to the Supabase endpoint.
- The system has no access to pump controls, chemical systems, or any site network beyond its own cellular/WiFi uplink.

## Operational Notes

- The logger runs as a systemd service, restarts automatically on failure, and logs to journald.
- Local SQLite buffer ensures no data loss during network outages of up to several hours (configurable retention).
- The `SIM_SCENARIO` environment variable and `SimulatorAdapter` allow full end-to-end testing without hardware. All seven scenarios can be exercised from a laptop.
- Sensor scaling is fully configurable via `SensorRange` — a 0-200 PSI transmitter on a high-pressure system is a config change, not a code change.
