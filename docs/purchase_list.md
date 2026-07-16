# SPC 2.0 Purchase List — POC Unit

This list covers one complete bench-test and field-deployable unit. Quantities are for a single device. Multiply for the trial fleet.

All prices are approximate USD as of mid-2026. Verify pricing before ordering.

---

## Core Compute

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | Raspberry Pi 4B | 4 GB RAM | $55 | Confirm availability — supply varies. 4GB preferred over 2GB for headroom. 8GB unnecessary. |
| 1 | SanDisk MAX Endurance microSD | 64 GB, Class 10 | $18 | Do not substitute with standard microSD — continuous 1 Hz writes will wear out a standard card within months. MAX Endurance or equivalent required. |
| 1 | Official Raspberry Pi USB-C power supply (5V 3A) | Bench use only | $8 | For bench testing only. Field units power Pi from HAT's 5V rail — confirm HAT can supply 2.5A to Pi before wiring field unit this way. |

---

## HAT / Analog Input

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | Sequent Microsystems Industrial Automation HAT | 8-layer stackable, 4-channel 4-20 mA input, 8 digital I/O, DIN-rail clip | $89 | Confirm part number — Sequent sells multiple HATs. The "Industrial Automation" 8-layer version with 4-20mA input is required. Verify HAT firmware is current before bench test. |

---

## Power Supply

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | Mean Well HDR-60-24 | 24 VDC, 2.5A, DIN-rail, 60W | $38 | Adequate for Pi + HAT + 4 two-wire transmitters (each draws ~25mA loop). If adding more devices later, size up to HDR-100-24. Verify input voltage matches site supply (120 VAC typical in US). |

---

## Enclosure

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | NEMA 4X polycarbonate enclosure | Polycase ZW-233-16 or equivalent, approx. 9"x7"x4" interior | $45 | Size must fit Pi, HAT stack, PSU, terminal blocks, and fuse block with wire routing room. Measure the HAT stack height with all layers before ordering. NEMA 4X for outdoor/pool room splash exposure. |
| 1 | DIN rail, 35mm | 12" length, cut to fit enclosure | $8 | Standard 35mm TS-35 rail. Cut to enclosure interior width. |

---

## Wiring and Protection

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 10 | DIN-rail terminal blocks | Phoenix Contact UTTB 2.5 or equivalent, 24 AWG rated | $25 | 2 terminals per sensor channel (+ and signal), 2 for pump dry contact, 2 for 24V bus. 10 is minimum; order 15 for margin. |
| 1 | 4-way fused terminal block or fuse block | TE Connectivity or Altech, 24VDC rated | $22 | One fused output per transmitter. Protects against wiring faults in the field. Confirm fuse amperage (0.5A per loop is typical for 4-20mA transmitters). |
| 1 | 3-circuit cable gland kit | M20 or M16 as needed for cable OD | $15 | One gland per cable entry: sensor cable bundle, power, and ethernet (if hardwired). Size to actual cable diameter. |
| 1 | DIN-rail end stops and mounting feet | Matching the DIN rail chosen | $6 | Prevents rail components sliding off ends. |
| 1 | Label maker tape / heat-shrink labels | P-touch TZe or equivalent | $12 | Label every terminal and wire at both ends. Non-negotiable for field maintainability. |
| 1 | Stainless M3/M4 hardware kit | Pan head, self-tapping for enclosure mounting | $8 | Stainless for wet/corrosive pool room environment. |

---

## Pressure Transmitters

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | P1: Compound pressure transmitter | -15 to +15 PSI, 4-20 mA, 2-wire, 1/4" NPT | $65 | Must handle vacuum (compound range). Confirm wetted materials are compatible with pool water chemistry if installed in a wet port. Ashcroft, Dwyer, or Omega are reliable options. |
| 2 | P2/P3: Gauge pressure transmitters | 0-100 PSI, 4-20 mA, 2-wire, 1/4" NPT | $55 ea | 0-100 PSI is a safe overrange for most commercial pool filter systems (typical operating 15-40 PSI). If the system operates above 60 PSI, confirm with filter manufacturer. Same model as P1 if compound range is acceptable — reduces spare parts complexity. |

---

## Flow Sensing

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | Clamp-on ultrasonic flow transmitter OR paddle-wheel insertion flow transmitter | 4-20 mA output, range 0-500 GPM (or site-appropriate max) | $150-$400 | Site-dependent. Clamp-on (e.g., Siemens SITRANS FS230, or Blue-White CHEM-FEED clamp style) is easiest to retrofit — no cutting pipe. Paddle-wheel (e.g., Seametrics) requires pipe tap — lower cost but more install effort. Confirm pipe material and ID before ordering clamp-on. PVC schedule 40 and schedule 80 have different calibration curves. |

---

## Pump Proof

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | Clamp-on current switch / solid-state relay output | CR Magnetics CR4110 or equivalent, adjustable trip point, SPST dry contact | $28 | Clamps around one motor lead — detects motor current without wiring into the control circuit. Confirm jaw size fits the motor cable. Adjust trip point above motor no-load current. |

---

## Test and Calibration Equipment

| # | Item | Spec / Part | Approx. Cost | Verify Before Buying |
|---|------|-------------|-------------|----------------------|
| 1 | 4-20 mA loop calibrator / simulator | Fluke 709 or equivalent, source and measure mode | $350 | Absolutely required for bench testing. Must simulate 4.0, 12.0, and 20.0 mA on each channel to verify scaling. Rent if not already owned. |
| 1 | Digital multimeter | Any quality DMM with mA range | (likely owned) | Used to verify loop wiring polarity and confirm mA readings independently from the calibrator. |

---

## Summary: Estimated POC Unit Cost

| Category | Approx. Cost |
|----------|-------------|
| Compute (Pi + SD + PSU) | $81 |
| HAT | $89 |
| Enclosure and DIN hardware | $53 |
| Wiring and protection | $88 |
| Pressure transmitters (×3) | $175 |
| Flow transmitter | $200 (midpoint) |
| Pump proof current switch | $28 |
| Test equipment (loop calibrator) | $350 |
| **Total (approx.)** | **$1,064** |

Excluding test equipment already owned, unit cost is approximately $714 per device. Volume pricing on transmitters and Pi compute will reduce this for a production fleet.

---

## Items That Are Site-Dependent

The following choices must be confirmed per installation site before ordering:

- Flow transmitter model and range (depends on pipe size, material, and expected flow range)
- Pressure transmitter range for P2/P3 (confirm max system pressure)
- Enclosure size (measure DIN stack height with all components fitted)
- Cable gland sizing (measure actual cable OD before ordering)
- PSU amperage (count all loop loads if adding extra sensors)
- Clamp-on current switch jaw size (measure motor cable OD)
