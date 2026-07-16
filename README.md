# SPC 2.0 — Smart Pool Circulation

Read-only IoT pool monitor. Raspberry Pi + 4-20 mA sensors → Python logger → Supabase → GREEN/YELLOW/RED dispatch status for pool service routing.

**This system observes. It does not control anything.**

---

## What It Does

Every 60 seconds the logger:
1. Averages 60 raw 1 Hz pressure and flow samples
2. Converts mA to engineering units (PSI, GPM)
3. Runs the GREEN/YELLOW/RED heuristic
4. POSTs the one-minute summary to Supabase
5. Buffers locally (SQLite) and retries if the network is down

Dispatchers see a live status board. Technicians are routed only when the data says so.

---

## Architecture

```
P1 Suction (4-20mA) ──┐
P2 Filter In (4-20mA)──┤──→ Raspberry Pi 4B ──→ Supabase Edge Function ──→ route_status_current
P3 Filter Out (4-20mA)─┤    Sequent HAT          readings_1min
Flow (4-20mA) ─────────┤    heuristics.py
Pump Proof (dry) ──────┘    local SQLite buffer
```

---

## Quickstart — Simulator Mode

No hardware required. Runs against your Supabase backend from any machine.

```bash
git clone https://github.com/PoolHombre/SPC20.git
cd SPC20
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -e .

cp .env.example .env
# Edit .env: set DEVICE_ID, DEVICE_TOKEN, SUPABASE_INGEST_URL

# Run green scenario (default)
python scripts/run_simulator.py

# Run a specific scenario
SIM_SCENARIO=red_loss_of_prime python scripts/run_simulator.py
```

Available scenarios:
- `green` — normal healthy pool
- `yellow_filter` — filter DP approaching service threshold
- `red_loss_of_prime` — pulsing flow, suction cavitation
- `red_no_flow` — pump running, no flow detected
- `fault_under` — under-range sensor (< 3.8 mA)
- `fault_over` — over-range sensor (> 20.5 mA)
- `invalid_p3_p2` — P3 >= P2 (physics violation)

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

---

## Dispatch Status Model

| Status | Action | Meaning |
|--------|--------|---------|
| GREEN | NO_VISIT | All normal — skip this pool today |
| YELLOW | ROUTE_TODAY | Something needs attention — include in route |
| RED | SEND_NOW | Active problem — dispatch immediately |

See `docs/system_overview.md` for the full heuristic logic and reason codes.

---

## Repository Layout

```
src/            Python logger source
tests/          pytest unit tests
supabase/
  migrations/   PostgreSQL schema (apply via supabase db push)
  functions/    Deno Edge Function (deploy via supabase functions deploy)
scripts/        install_service.sh (Pi), run_simulator.py (dev)
systemd/        spc20-logger.service unit file
docs/           System overview, purchase list, wiring, test plans, trial plan
```

---

## Hardware

Raspberry Pi 4B + Sequent Microsystems Industrial Automation HAT (4-channel 4-20 mA). Full BOM in `docs/purchase_list.md`. Wiring in `docs/wiring_diagram.md`.

---

## Backend Setup

1. Create a Supabase project
2. Apply the migration: `supabase db push` or use the apply_migration MCP tool
3. Deploy the Edge Function: `supabase functions deploy spc20-ingest`
4. Add your device to the `devices` table with the SHA-256 hash of its token
5. Set environment variables in `.env`

---

## Field Deployment

1. Complete bench acceptance test (`docs/bench_test_plan.md`) — all 17 tests must PASS
2. Complete site survey (`docs/field_install_checklist.md`)
3. Run `scripts/install_service.sh` on the Pi
4. Complete field installation checklist
5. Run 24-hour soak

---

## License

Proprietary — Poolsure / AquaSol internal use only.
