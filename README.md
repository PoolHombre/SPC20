# SPC 2.0 — Smart Pool Circulation Monitor

Read-only IoT pool monitor for commercial swimming pools.
Raspberry Pi + 4-20 mA sensors → Python logger → Supabase → GREEN / YELLOW / RED dispatch status for pool service routing.

**This system observes. It does not control anything.**

---

## What It Does

Every 60 seconds the logger:
1. Averages 60 raw 1 Hz pressure and flow samples
2. Classifies sensor quality (GOOD / LOOP_LOW_FAULT / LOOP_HIGH_FAULT / …)
3. Converts mA to engineering units (PSI, GPM)
4. Runs the GREEN / YELLOW / RED heuristic
5. POSTs the one-minute summary to Supabase (with local SQLite retry queue)
6. Updates the local Flask dashboard

Dispatchers see a live status board. Technicians are routed only when the data says so.

---

## Build Structure

| Build | Phase | Hardware | Goal |
|-------|-------|----------|------|
| 1A | Bench | Pi + HAT on desk, bench power supply, sensor simulators or 4-20mA signal generators | Software + sensor chain verified in controlled environment |
| 1B | Yard | 1A hardware moved to outdoor enclosure at yard facility, real sensors in bucket/pipe rig | Weatherproofing, real signals, 48-hr unattended run |
| 1C | Field | 1B hardware installed at customer site | First live commercial pool, full trial, Build 2 decision |

See `docs/build1_phase_gates.md` for measurable pass criteria at each gate.

---

## Dispatch Status Model

| Status | Action | Meaning |
|--------|--------|---------|
| GREEN | NO_VISIT | All normal — no visit needed |
| YELLOW | ROUTE_TODAY | Needs attention — include in today's route |
| RED | SEND_NOW | Active problem — dispatch immediately |

Reason codes and recommended checks: `docs/heuristics.md`.

---

## Quick Start — Development (Simulator Mode)

No hardware required. Runs against your Supabase backend or with a local mock.

```bash
git clone https://github.com/PoolHombre/SPC20.git
cd SPC20
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"

cp .env.example .env
# Edit .env: set DEVICE_ID, DEVICE_TOKEN, SUPABASE_INGEST_URL
# Leave SENSOR_ADAPTER=simulator for dev

# Run the logger service (green scenario by default)
python -m spc20.services.logger_service

# Or run a specific scenario
SIM_SCENARIO=red_loss_of_prime python -m spc20.services.logger_service
```

Available simulator scenarios: `green`, `yellow_filter`, `red_loss_of_prime`, `red_no_flow`, `fault_under`, `fault_over`, `invalid_p3_p2`.

---

## Quick Start — Local Dashboard

```bash
# In a second terminal:
FLASK_APP="spc20.web.app:create_app()" flask run --port 8080
# Or with gunicorn (production-style):
gunicorn -w 2 -b 0.0.0.0:8080 "spc20.web.app:create_app()"

# Open http://localhost:8080
# API: http://localhost:8080/api/status
```

Dashboard docs: `docs/local_tech_dashboard.md`.

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Supabase Setup

1. Create a Supabase project at supabase.com.
2. Apply schema migrations:
   ```bash
   supabase db push
   # Or via the MCP apply_migration tool in Claude Code
   ```
3. Deploy the Edge Function:
   ```bash
   supabase functions deploy spc20-ingest
   ```
4. Add your device row to the `devices` table (device_id + SHA-256 of device token).
5. Set `SUPABASE_INGEST_URL` in `.env`.
6. **Never** set `SUPABASE_SERVICE_ROLE_KEY` on the device.

---

## Raspberry Pi Deployment

Full steps: `DEPLOYMENT_STEPS.md`.

Short form:
```bash
# From dev machine:
scp -r . pi@192.168.1.100:/opt/spc20/
ssh pi@192.168.1.100
cd /opt/spc20
pip install -e .
sudo cp systemd/spc20-logger.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now spc20-logger.service
```

---

## Architecture

```
P1 Suction (4-20 mA)  ──┐
P2 Filter In (4-20 mA) ──┤── Sequent HAT ── Pi GPIO ── spc20.adapters.sequent
P3 Filter Out (4-20 mA)──┤
Flow (4-20 mA) ──────────┤
Pump Proof (dry contact) ─┘

logger_service (1 Hz sample → 60-sec summarise → heuristics.evaluate)
    │
    ├── LocalBuffer (SQLite WAL) ─── uploader (retry queue)
    │                                     └── Supabase Edge Function → readings_1min
    └── web.app (Flask) ── /api/status, /api/live, /api/health
```

---

## Repository Layout

```
src/spc20/
  adapters/         SensorAdapter base + SimulatorAdapter + SequentAdapter
  services/         logger_service.py — main loop
  web/              Flask app factory, auth, templates
  scaling.py        4-20 mA → engineering units
  quality.py        Signal quality state machine
  aggregation.py    60-sample → 1-min summary
  calibration.py    ambient_zero and static_baseline modes
  heuristics.py     GREEN / YELLOW / RED dispatch logic
  buffer.py         SQLite local buffer + retry queue
  config.py         DeviceConfig from env vars
tests/              pytest test suite
supabase/
  migrations/       PostgreSQL schema
  functions/        Deno Edge Function (spc20-ingest)
systemd/            Service unit files
docs/               Trial plans, wiring, calibration, heuristics docs
scripts/            Pi installer, simulator runner, AP setup notes
```

---

## License

Proprietary — Poolsure / AquaSol internal use only.
