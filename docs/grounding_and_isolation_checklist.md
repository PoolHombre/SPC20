# Grounding and Isolation Checklist — SPC 2.0

Complete this checklist during enclosure assembly and again during field installation.

---

## Chassis Ground

| Item | Done | Notes |
|------|------|-------|
| Enclosure is metal or has a grounded DIN rail | | |
| DIN rail bonded to enclosure back panel with star washer | | |
| Enclosure grounding lug connected to site electrical panel ground (green/yellow wire, min 12 AWG) | | |
| PSU chassis (if metal) bonded to enclosure | | |
| All bond connections verified with DMM: < 1 Ω between each bonded point and earth ground | | |

---

## Signal Ground

| Item | Done | Notes |
|------|------|-------|
| 24 VDC common bus (0V / -) connected to earth ground at PSU minus terminal only | | |
| No additional 0V-to-earth connections (single-point ground prevents ground loops) | | |
| HAT GND pin connected to 24V common bus at one point | | |
| Verified: < 0.5 V between 24V common and earth ground at HAT | | |

---

## Loop Isolation

| Item | Done | Notes |
|------|------|-------|
| Each transmitter loop has its own fused supply (no shared fuse between channels) | | |
| Transmitter signal shields (if present) terminated at enclosure end only — not at transmitter | | |
| Shield NOT grounded at both ends (prevents shield current from flowing through signal conductor) | | |
| No transmitter loop connected to earth at the transmitter end | | |
| Pump DI wiring uses dry contact — no external voltage applied to DI terminals | | |

---

## Panel Bonding (Field Only)

| Item | Done | Notes |
|------|------|-------|
| SPC enclosure bonded to existing electrical panel ground at field site | | |
| Any metallic conduit bonded to panel ground | | |
| If conduit is non-metallic (PVC): green ground conductor included inside conduit | | |
| Pool electrical bonding grid continuity verified — no SPC enclosure components connect to pool bonding grid (signal interference risk) | | |

---

## Post-Installation Verification

| Test | Method | Pass Criterion |
|------|--------|----------------|
| Ground continuity | DMM resistance from enclosure lug to panel ground | < 1 Ω |
| Loop isolation | DMM AC voltage from loop common to earth | < 1 V AC |
| No stray current | Clamp meter around signal cable bundle | < 5 mA |
| P1 mA stable | Read HAT AI-1 for 60 sec at known pressure | Stddev < 0.05 mA |
| No ground loop hum | FFT or DMM AC on signal wire | < 0.1 mA AC ripple |

---

## Common Problems

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| 4-20 mA reading drifts ±1 mA with other equipment | Ground loop — multiple 0V-to-earth connections | Remove extra earth bonds; keep single-point |
| Constant 4 mA on a channel | Reversed loop polarity | Swap + and signal wires |
| Noisy reading (high stddev) | Unshielded cable near VFD | Reroute away from VFD; add shielded cable |
| All channels read same incorrect value | I2C HAT address conflict | Check HAT DIP switch; verify I2C address in config |
| DI always high | External voltage on DI terminals | Remove — DI must be dry contact only |
