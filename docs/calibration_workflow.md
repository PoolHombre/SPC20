# Calibration Workflow — SPC 2.0

Calibration compensates for transmitter zero offsets and static head differences between sensors. Raw mA values are always preserved — calibration only adjusts the engineering-unit output used by heuristics.

---

## Mode A — ambient_zero

### When to Use

- Initial installation: before the first trial run.
- After a transmitter is replaced.
- Any time the heuristics produce suspicious readings with the system at rest.
- Whenever a transmitter is known to be isolated/vented and can be confirmed at true zero.

### Pre-conditions

- The transmitter must be physically isolated from the process (vented to atmosphere, or isolated valve closed).
- The pump must be off.
- System must be stable for at least 60 seconds before starting.

### Procedure

1. Stop the pump and confirm pump_running = False in /api/status.
2. Close the isolation valve on the pressure tap being calibrated (if equipped).
3. Vent the transmitter to atmosphere (open vent plug or remove impulse line cap).
4. Wait 60 seconds for the reading to stabilize.
5. In the dashboard or via CLI, trigger ambient_zero for the channel:

   ```bash
   # Via dashboard: POST /api/calibration/ambient-zero {"channel": "p1"}
   # Via CLI (direct):
   python -c "
   from spc20.calibration import Calibrator
   from spc20.config import load_config
   c = Calibrator(load_config())
   # Supply a callable that returns the current mA reading from your adapter
   result = c.ambient_zero(lambda: adapter.read().p1_ma, channel='p1')
   print(result)
   "
   ```

6. Inspect the result:
   - `accepted = True` means stddev was within 0.05 mA — offset stored.
   - `accepted = False` means the signal was unstable. Check for:
     - Air movement across an open vent
     - Vibration from nearby equipment
     - Noisy electrical environment
   - Re-run until accepted.

7. Reconnect the transmitter (close vent, open isolation valve).
8. Confirm the reading at ambient is now ≈ 4.00 mA in /api/status.

### Acceptance Criteria

| Metric | Pass |
|--------|------|
| accepted | True |
| stddev | ≤ 0.05 mA |
| offset_value | Non-null, stored in calibration_events |
| Post-calibration reading at zero | 4.00 ± 0.05 mA |

---

## Mode B — static_baseline

### When to Use

- Before the first trial run, with the pump confirmed off.
- When there is an unexplained P2/P3 differential at pump-off (should be zero or close to static head difference).
- Captures the static-head contribution of the pipe geometry so the DP calculation can be corrected.

### Pre-conditions

- Pump must be confirmed off (pump_running = False).
- System must be fully de-pressurized and at equilibrium (allow 2 minutes after pump stop).

### Procedure

1. Confirm pump is off and pump_running = False in /api/status.
2. Allow 2 minutes for system to equilibrate.
3. Trigger static_baseline:

   ```bash
   # Via dashboard: POST /api/calibration/static-baseline {}
   # Or via CLI:
   python -c "
   from spc20.calibration import Calibrator
   from spc20.config import load_config
   c = Calibrator(load_config())
   result = c.static_baseline(
     read_p2_ma=lambda: adapter.read().p2_ma,
     read_p3_ma=lambda: adapter.read().p3_ma,
     pump_running=False,
   )
   print(result)
   "
   ```

4. Inspect result:
   - `static_p23_offset` = p2_mean - p3_mean (in mA). Non-zero if taps are at different elevations.
   - `p2_static_mean` and `p3_static_mean` stored in calibration_events.
   - `accepted` is always True for static_baseline (pump-off guarantees validity).

5. Record the offset in notes for reference.

### Acceptance Criteria

| Metric | Pass |
|--------|------|
| accepted | True (always) |
| p2_sd and p3_sd | ≤ 0.10 mA (higher than ambient_zero since pump is off but system may have minor thermal drift) |
| static_p23_offset | Stored non-null |
| Physical interpretation | Offset direction consistent with physical elevation difference between P2 and P3 taps |

---

## Calibration Event Records

All calibration events are stored in `calibration_events` in the local SQLite DB and uploaded to Supabase when connectivity permits. Query recent events:

```bash
sqlite3 /var/lib/spc20/spc20.db \
  "SELECT id, channel, mode, offset_value, accepted, created_at FROM calibration_events ORDER BY id DESC LIMIT 10;"
```

---

## Re-Calibration Policy

| Trigger | Action |
|---------|--------|
| Transmitter replaced | ambient_zero on affected channel |
| Heuristics firing unexpectedly at known-normal conditions | ambient_zero on suspect channel |
| System moved or pipes modified | static_baseline (and ambient_zero if transmitters disturbed) |
| Annual scheduled maintenance | ambient_zero on all channels |
| stddev rejection | Investigate noise source, re-run |
