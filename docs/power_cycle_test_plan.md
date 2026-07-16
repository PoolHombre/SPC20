# Power Cycle Test Plan — SPC 2.0

## Purpose

Verify that the device survives a hard power cut (no graceful shutdown) without DB corruption, data loss beyond the in-flight sample, or service hang after restart. This test must pass before any outdoor or field deployment.

---

## Pre-conditions

- Device is running in normal operation (SENSOR_ADAPTER=simulator or real sensors)
- At least 5 minutes of data have been written to the local DB
- Supabase connectivity is active so the upload queue can be observed

---

## Test Procedure

### Step 1 — Baseline

```bash
ssh pi@<pi-ip>

# Record current state
ROW_COUNT=$(sqlite3 /var/lib/spc20/spc20.db "SELECT COUNT(*) FROM telemetry_queue;")
PENDING=$(sqlite3 /var/lib/spc20/spc20.db "SELECT COUNT(*) FROM telemetry_queue WHERE uploaded=0;")
echo "Pre-cut rows: $ROW_COUNT, pending uploads: $PENDING"

# Note current spc20-logger PID
systemctl status spc20-logger.service | grep "Main PID"

# Note last observed_at in DB
sqlite3 /var/lib/spc20/spc20.db "SELECT MAX(observed_at) FROM telemetry_queue;"
```

### Step 2 — Hard Power Cut

Pull the power supply cord or trip the circuit breaker feeding the device. Do NOT use `sudo shutdown` or `sudo systemctl stop` — this test must simulate an uncontrolled power loss.

Wait 5 seconds.

### Step 3 — Restore Power

Reconnect power. Start timer.

### Step 4 — Verify Boot and Service

```bash
# SSH back in (wait up to 2 minutes for boot)
ssh pi@<pi-ip>

# Check spc20-logger service started
systemctl status spc20-logger.service
# Expect: active (running)

# Check startup time
systemctl show spc20-logger.service --property=ActiveEnterTimestamp
```

**Pass criterion:** Service active within 2 minutes of power restore.

### Step 5 — DB Integrity

```bash
sqlite3 /var/lib/spc20/spc20.db "PRAGMA integrity_check;"
```

**Pass criterion:** `ok` returned. Any other output is a FAIL — escalate immediately.

### Step 6 — Data Continuity

```bash
POST_ROW_COUNT=$(sqlite3 /var/lib/spc20/spc20.db "SELECT COUNT(*) FROM telemetry_queue;")
echo "Post-cut rows: $POST_ROW_COUNT"
# Expected: >= pre-cut row count (WAL recovery may add back any in-flight writes)
# Acceptable: 0-1 rows lost (single in-flight write at moment of cut)
# FAIL: row count decreased by > 1
```

### Step 7 — Heuristics Resuming

```bash
# Wait 2 minutes for logger to produce first post-boot reading
sleep 120
curl -s http://localhost:8080/api/live | python3 -m json.tool
# Expect: status is GREEN/YELLOW/RED (not UNKNOWN)
# FAIL if status = UNKNOWN after 3 minutes
```

### Step 8 — Upload Queue Drains

```bash
# Wait for upload cycle (up to 5 minutes)
sleep 300
PENDING_AFTER=$(sqlite3 /var/lib/spc20/spc20.db "SELECT COUNT(*) FROM telemetry_queue WHERE uploaded=0;")
echo "Pending after drain: $PENDING_AFTER"
# Pass: pending_after <= pending_before (queue is draining, not growing)
# Ideal: 0 if Supabase connectivity is active
```

---

## Pass / Fail Criteria Summary

| Check | Pass Criterion | Actual | Result |
|-------|---------------|--------|--------|
| Service restart | Active within 2 min | | |
| DB integrity_check | `ok` | | |
| Row count | >= pre-cut count - 1 | | |
| Heuristics active | Status not UNKNOWN within 3 min | | |
| Upload queue | pending_after <= pending_before | | |

---

## Failure Handling

| Failure | Action |
|---------|--------|
| DB integrity_check fails | Do NOT proceed to yard/field — investigate WAL configuration. Check /var/lib/spc20 filesystem mount |
| Service does not restart | Check systemctl enable was applied; check spc20-preflight.sh exit code |
| Heuristics stuck at UNKNOWN | Check adapter initialization; check if logger crashed (journalctl -u spc20-logger) |
| Row count decreased by > 1 | WAL not configured correctly — verify PRAGMA journal_mode=WAL in buffer.py |

---

## Record Results Here

Power cut time: _______________
Power restore time: _______________
Service active time: _______________
Tester: _______________
Device ID: _______________
Trial phase: _______________
Outcome: PASS / FAIL
Notes:
