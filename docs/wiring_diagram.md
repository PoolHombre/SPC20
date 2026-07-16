# SPC 2.0 Wiring Diagram

Text-based wiring reference. Use this alongside the Sequent Microsystems HAT datasheet to wire the physical unit.

---

## Power Distribution

```
120 VAC (site supply)
    │
    └──→ [Mean Well HDR-60-24 DIN PSU]
              │ 24 VDC output (+)  → [Fuse Block IN+]
              │ 24 VDC output (-)  → [Fuse Block IN- / Common Bus]
              │
         [Fuse Block — 4-way, 0.5A per channel]
              │
              ├─ FUSE 1 (0.5A) ──→ [TB-1+]  ──→ P1 Transmitter (+24V loop supply)
              ├─ FUSE 2 (0.5A) ──→ [TB-3+]  ──→ P2 Transmitter (+24V loop supply)
              ├─ FUSE 3 (0.5A) ──→ [TB-5+]  ──→ P3 Transmitter (+24V loop supply)
              └─ FUSE 4 (0.5A) ──→ [TB-7+]  ──→ Flow Transmitter (+24V loop supply)

         [Common Bus (0V / -)]
              ├─────────────────→ Pi/HAT GND (via HAT power connector)
              ├─────────────────→ [TB-2-]  ──→ P1 Transmitter (signal return)
              ├─────────────────→ [TB-4-]  ──→ P2 Transmitter (signal return)
              ├─────────────────→ [TB-6-]  ──→ P3 Transmitter (signal return)
              └─────────────────→ [TB-8-]  ──→ Flow Transmitter (signal return)

         HAT 5V rail ──→ Raspberry Pi 4B (USB-C or HAT GPIO 5V/GND pins)
```

---

## Analog Input Wiring — 4-20 mA Two-Wire Loops

Each transmitter is a 2-wire device. The HAT supplies loop power through the + terminal; the transmitter modulates current (4-20 mA) on the return wire back to the HAT analog input. The HAT has an internal burden resistor that converts the current to a voltage it can read.

```
HAT Analog Input Channel Layout (Sequent Industrial HAT)

AI-1 ────────────────────────────────────────────────────────────────────
  HAT AI-1 (+) ──→ [TB-1+] ──→ Fuse 1 (0.5A) ──→ 24V PSU (+)
                                  ↓
                              [P1: Compound Pressure Transmitter]
                              -15 to +15 PSI, 2-wire, 4-20 mA
                                  ↓
  HAT AI-1 (SIG) ←── [TB-1S] ←── P1 signal wire (4-20 mA return)
  (HAT measures current on SIG wire; common 0V shared with PSU -)

AI-2 ────────────────────────────────────────────────────────────────────
  HAT AI-2 (+) ──→ [TB-3+] ──→ Fuse 2 (0.5A) ──→ 24V PSU (+)
                                  ↓
                              [P2: Filter Inlet Pressure Transmitter]
                              0-100 PSI, 2-wire, 4-20 mA
                                  ↓
  HAT AI-2 (SIG) ←── [TB-3S] ←── P2 signal wire

AI-3 ────────────────────────────────────────────────────────────────────
  HAT AI-3 (+) ──→ [TB-5+] ──→ Fuse 3 (0.5A) ──→ 24V PSU (+)
                                  ↓
                              [P3: Filter Outlet Pressure Transmitter]
                              0-100 PSI, 2-wire, 4-20 mA
                                  ↓
  HAT AI-3 (SIG) ←── [TB-5S] ←── P3 signal wire

AI-4 ────────────────────────────────────────────────────────────────────
  HAT AI-4 (+) ──→ [TB-7+] ──→ Fuse 4 (0.5A) ──→ 24V PSU (+)
                                  ↓
                              [Flow Transmitter]
                              0-500 GPM (site-appropriate), 2-wire, 4-20 mA
                                  ↓
  HAT AI-4 (SIG) ←── [TB-7S] ←── Flow signal wire
```

---

## Digital Input Wiring — Pump Proof

The pump proof uses a clamp-on current switch (e.g., CR Magnetics CR4110) clamped around one motor lead. When the motor is running, the current switch closes its dry contact output.

```
DI-1 ────────────────────────────────────────────────────────────────────
  HAT DI-1 (+) ──→ [TB-9+]  ──→ Current Switch COM
  HAT DI-1 (-)  ──→ [TB-9-]  ──→ Current Switch NO (Normally Open)

  When motor current is detected:
    Contact closes → DI-1 reads HIGH → pump_running = True

  Note: The current switch output is a dry contact (voltage-free).
  The HAT supplies the wetting voltage for the digital input internally.
  Do NOT apply external voltage to DI-1 terminals.
```

---

## Terminal Block Summary

| TB # | Label | Connection |
|------|-------|-----------|
| TB-1+ | P1 LOOP+ | Fuse 1 → P1 transmitter + |
| TB-1S | P1 SIG | P1 transmitter signal return → HAT AI-1 |
| TB-2- | COMMON | 0V bus |
| TB-3+ | P2 LOOP+ | Fuse 2 → P2 transmitter + |
| TB-3S | P2 SIG | P2 transmitter signal return → HAT AI-2 |
| TB-4- | COMMON | 0V bus |
| TB-5+ | P3 LOOP+ | Fuse 3 → P3 transmitter + |
| TB-5S | P3 SIG | P3 transmitter signal return → HAT AI-3 |
| TB-6- | COMMON | 0V bus |
| TB-7+ | FL LOOP+ | Fuse 4 → Flow transmitter + |
| TB-7S | FL SIG | Flow transmitter signal return → HAT AI-4 |
| TB-8- | COMMON | 0V bus |
| TB-9+ | PUMP DI+ | HAT DI-1 + → Current switch COM |
| TB-9- | PUMP DI- | HAT DI-1 - → Current switch NO |

---

## Notes

- All field wiring to terminal blocks should be 18 AWG stranded, shielded where possible for long cable runs (over 10 feet). Ground shield at the enclosure end only.
- Label both ends of every wire before installation. Use the TB label plus the channel name (e.g., "TB-1+ / P1 LOOP+").
- The 24 VDC common bus (0V) and the HAT GND must be tied together at one point to establish a common reference. This is typically done at the PSU - terminal.
- Verify polarity on all transmitters before applying power. Reverse polarity on a 4-20 mA loop will not damage most transmitters but will read 4 mA constantly.
- The HAT register map and I2C addresses must be confirmed against the specific HAT firmware version. See `src/sensors.py` SequentAdapter for the current address assumptions and update if your HAT revision differs.
