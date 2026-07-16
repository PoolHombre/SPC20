# SPC 2.0 Purchase List — POC Unit

This list covers one complete bench-test and field-deployable unit. Quantities are for a single device. Multiply for the trial fleet.

All prices are approximate USD as of mid-2026. Verify pricing before ordering.

---

## Bench Core

Items required for Build 1A (Bench) operation.

| # | Item | Spec / Part | Approx. Cost | Notes |
|---|------|-------------|-------------|-------|
| 1 | Raspberry Pi 4B | 4 GB RAM | $55 | 4 GB preferred; 8 GB unnecessary |
| 1 | SanDisk MAX Endurance or industrial pSLC microSD | 64 GB | $18 | Do NOT use standard microSD — 1 Hz continuous writes require endurance card |
| 1 | Official RPi USB-C power supply 5V 3A | Bench use only | $8 | Field units power Pi from HAT 5V rail |
| 1 | Sequent Microsystems Industrial Automation HAT | 4-channel 4-20 mA, 8 DI, DIN-rail clip | $89 | Confirm "Industrial Automation" 8-layer HAT specifically |
| 1 | Mean Well HDR-60-24 | 24 VDC 2.5A DIN-rail | $38 | Sufficient for 4 two-wire transmitter loops + Pi |
| 1 | Fluke 709 or equivalent 4-20 mA loop calibrator | Source and measure mode | $350 | Rent if not owned — required for bench scaling verification |
| 1 | Digital multimeter | mA range | (likely owned) | Loop polarity and cross-check |

**Bench subtotal (excl. owned DMM): ~$558**

---

## Yard Add-ons

Additional items for Build 1B (Yard) outdoor enclosure.

| # | Item | Spec / Part | Approx. Cost | Notes |
|---|------|-------------|-------------|-------|
| 1 | NEMA 4X polycarbonate enclosure | ~9"×7"×4" interior, e.g. Polycase ZW-233-16 | $45 | Measure HAT stack height before ordering |
| 1 | DIN rail 35mm TS-35 | 12" cut to enclosure width | $8 | |
| 10 | DIN-rail terminal blocks | Phoenix UTTB 2.5 or equiv, 24 AWG rated | $25 | Order 15 for margin |
| 1 | 4-way fused terminal block | 0.5A per loop, 24 VDC rated | $22 | |
| 3 | Cable glands M20 or M16 | Size to actual cable OD | $15 | One per cable entry |
| 1 | DIN-rail end stops and mounting feet | Match rail chosen | $6 | |
| 1 | Label maker tape / heat-shrink labels | P-touch TZe or heat-shrink | $12 | Label both ends of every wire |
| 1 | Stainless M3/M4 hardware kit | Pan head, self-tapping | $8 | Stainless for pool room environment |

**Yard add-on subtotal: ~$141**

---

## Field Add-ons

Additional items required for customer-premises installation (Build 1C).

| # | Item | Spec / Part | Approx. Cost | Notes |
|---|------|-------------|-------------|-------|
| 1 | UPS / battery backup | DIN-rail 24 VDC UPS, e.g. Phoenix Contact QUINT-UPS | $220 | Min 30 min runtime at full load |
| 1 | Clamp-on ultrasonic flow transmitter OR paddle-wheel insertion | 4-20 mA, 0-500 GPM (or site-appropriate) | $150–$400 | Site-dependent — confirm pipe size and material before ordering |
| 1 | P1: Compound pressure transmitter | -15 to +15 PSI, 4-20 mA, 2-wire, 1/4" NPT | $65 | Must handle vacuum |
| 2 | P2/P3: Gauge pressure transmitters | 0-100 PSI, 4-20 mA, 2-wire, 1/4" NPT | $55 ea | Ashcroft, Dwyer, or Omega |
| 1 | Pump proof current switch | CR Magnetics CR4110 or equiv, SPST dry contact | $28 | Clamps on motor lead |
| 1 | Conduit and fittings | 3/4" EMT or liquid-tight flex, as required | $30 | Site-dependent length |
| 4 | 1/4" NPT pressure taps with isolation valves | Swagelok or Parker, stainless | $40 ea | Allows transmitter removal without system drain |

**Field add-on subtotal: ~$768 (midpoint flow)**

---

## Field Hardening

Items for long-term reliability in unattended field operation.

| # | Item | Spec / Part | Approx. Cost | Notes |
|---|------|-------------|-------------|-------|
| 1 | Industrial pSLC SD card upgrade | Industrial Innodisk or Swissbit 32 GB pSLC | $45 | Replace standard SD; OverlayFS extends any card |
| 1 | Hardware watchdog HAT add-on or RPi built-in WDT | dtparam=watchdog=on in config.txt (no cost) | $0–$25 | Built-in WDT free; external HAT adds belt-and-suspenders |
| 1 | Tailscale or ZeroTier remote access | Annual license or self-hosted | $0–$48/yr | Required for remote SSH access to field device |
| 1 | Silica gel desiccant packets | 10g per enclosure | $5 | Replace annually |

**Hardening subtotal: ~$75–$120**

---

## Optional Tools / Deferred

| # | Item | Notes |
|---|------|-------|
| 1 | Raspberry Pi 5 (upgrade path) | Faster, but Pi 4B is sufficient for Build 1 |
| 1 | Cellular modem (LTE) | For sites without reliable Wi-Fi — deferred to Build 2 |
| 1 | Suction-side flow transmitter (second flow meter) | Provides redundancy — deferred |
| 1 | Temperature sensor (pool water) | Future feature for chemical dosing correlation |
| 1 | Portable oscilloscope | Useful for diagnosing noisy 4-20 mA loops |
| 1 | Pressure gauge (0-100 PSI, calibrated) | For field verification of transmitter readings |

---

## Summary — Estimated Costs

| Phase | Subtotal |
|-------|---------|
| Bench Core | ~$558 |
| Yard Add-ons | ~$141 |
| Field Add-ons | ~$768 |
| Field Hardening | ~$98 |
| **Total per unit** | **~$1,565** |

Excluding owned test equipment (~$350), unit cost is approximately **$1,215 per field-deployed device**. Volume pricing on transmitters, Pi compute, and enclosures will reduce this at scale.

---

## Site-Dependent Decisions (Confirm Before Ordering)

- Flow transmitter model and range — depends on pipe size, material, and max GPM
- Pressure transmitter range for P2/P3 — confirm max system pressure with filter manufacturer
- Enclosure size — measure DIN stack with all components assembled
- Cable gland size — measure actual cable OD at the gland entry point
- Conduit type and length — determined by site routing
- UPS runtime — size to site's average power outage duration history
