# SPC 2.0 — Deployment Steps

---

## 1. Local Development Setup

```bash
git clone https://github.com/PoolHombre/SPC20.git
cd SPC20
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -e ".[dev]"
cp .env.example .env
# Edit .env — set DEVICE_ID, DEVICE_TOKEN, SUPABASE_INGEST_URL
# Leave SENSOR_ADAPTER=simulator for local dev

# Run simulator
python -m spc20.services.logger_service

# Run tests
pytest tests/ -v
```

---

## 2. Supabase — Apply Migrations

Requires Supabase CLI installed and linked to your project.

```bash
# Link CLI to your project (once)
supabase login
supabase link --project-ref <your-project-ref>

# Apply all pending migrations
supabase db push

# Or apply a specific migration
supabase migration up 20260716000001_spc20_initial
supabase migration up 20260716000002_spc20_hardening
```

Verify in Supabase table editor: `readings_1min`, `trial_runs`, `calibration_events` should exist.

---

## 3. Supabase — Deploy Edge Function

```bash
supabase functions deploy spc20-ingest
```

Set function secrets in Supabase dashboard:
- `DEVICE_TOKEN_SALT` (used to verify device tokens)

Test the function:
```bash
curl -X POST \
  https://<project-ref>.supabase.co/functions/v1/spc20-ingest \
  -H "Authorization: Bearer <DEVICE_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"spc20-b1-bench-0001","observed_at":"2026-07-16T00:00:00Z","pump_running":true}'
```

---

## 4. Raspberry Pi — Initial Setup

### 4a — Image the SD card

- Download Raspberry Pi OS Bookworm Lite (64-bit)
- Use Raspberry Pi Imager
- Pre-configure: hostname, SSH enabled, Wi-Fi credentials, username `pi`

### 4b — First boot

```bash
# From dev machine — verify SSH works
ssh pi@<pi-ip>
```

### 4c — Install dependencies on Pi

```bash
sudo apt-get update && sudo apt-get install -y python3-pip python3-venv git
```

### 4d — Copy project to Pi

From dev machine:
```bash
scp -r . pi@<pi-ip>:/opt/spc20/
```

Or clone on Pi:
```bash
ssh pi@<pi-ip>
git clone https://github.com/PoolHombre/SPC20.git /opt/spc20/
```

### 4e — Install Python package

```bash
ssh pi@<pi-ip>
cd /opt/spc20
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 4f — Configure environment

```bash
sudo mkdir -p /etc/spc20 /var/lib/spc20
sudo cp /opt/spc20/.env.example /etc/spc20/.env
sudo nano /etc/spc20/.env
# Set: DEVICE_ID, DEVICE_TOKEN, SUPABASE_INGEST_URL, SENSOR_ADAPTER=sequent
```

Secure the env file:
```bash
sudo chown root:pi /etc/spc20/.env
sudo chmod 640 /etc/spc20/.env
```

### 4g — Enable systemd service

```bash
sudo cp /opt/spc20/systemd/spc20-logger.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable spc20-logger.service
sudo systemctl start spc20-logger.service
# Check status
sudo systemctl status spc20-logger.service
journalctl -u spc20-logger.service -f
```

---

## 5. Power Cycle Test

See `docs/power_cycle_test_plan.md` for full procedure. Short form:

```bash
# Record current DB row count
ssh pi@<pi-ip>
sqlite3 /var/lib/spc20/spc20.db "SELECT COUNT(*) FROM telemetry_queue;"

# Hard power cut (pull power)
# ... wait 5 seconds ...
# Restore power

# After reboot — verify
ssh pi@<pi-ip>
sudo systemctl status spc20-logger.service
sqlite3 /var/lib/spc20/spc20.db "PRAGMA integrity_check;"
# Expect: ok
sqlite3 /var/lib/spc20/spc20.db "SELECT COUNT(*) FROM telemetry_queue;"
# Row count should be >= pre-cut count (no data loss after WAL recovery)
```

---

## 6. Dashboard Access

Local access (on same network as device):
```bash
# From browser
http://<pi-ip>:8080
http://<pi-ip>:8080/api/status
http://<pi-ip>:8080/api/health
```

Remote access (via Tailscale or SSH tunnel):
```bash
ssh -L 8080:localhost:8080 pi@<pi-ip>
# Then: http://localhost:8080
```

---

## 7. Verify Upload Queue Drains

```bash
# On Pi:
watch -n 10 "sqlite3 /var/lib/spc20/spc20.db 'SELECT COUNT(*) FROM telemetry_queue WHERE uploaded=0'"
# Count should decrease as uploads succeed and stay at 0 when connected
```

---

## 8. Update Deployed Code

```bash
# From dev machine:
scp -r src/ pi@<pi-ip>:/opt/spc20/src/
ssh pi@<pi-ip>
cd /opt/spc20
source .venv/bin/activate
pip install -e .
sudo systemctl restart spc20-logger.service
```
