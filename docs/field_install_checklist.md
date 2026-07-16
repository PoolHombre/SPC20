# SPC 2.0 Field Installation Checklist

Complete each section in order. Do not proceed to the next section until all items in the current section are checked.

---

## Section 1: Site Survey (Before Parts Are Ordered)

Complete this survey before purchasing site-specific components. Some items affect which parts to order.

### Hydraulics

- [ ] Pipe material identified (PVC, CPVC, copper, other): _______________
- [ ] Pipe nominal size at flow meter location: _______________
- [ ] Pipe inside diameter measured (clamp-on flow meters need exact ID): _______________
- [ ] Minimum straight pipe run upstream of flow meter available (typically 10x pipe diameter): ___ inches
- [ ] P1 tap location identified on suction line (before pump): _______________
- [ ] P2 tap location identified (filter inlet, after pump): _______________
- [ ] P3 tap location identified (filter outlet): _______________
- [ ] Existing 1/4" NPT gauge ports available at P1/P2/P3 locations (yes/no): _______________
- [ ] Filter type (sand, cartridge, DE): _______________
- [ ] Filter manufacturer and model (for DP service spec confirmation): _______________
- [ ] Maximum expected system pressure at P2/P3 (to confirm 0-100 PSI transmitter range): ___ PSI

### Electrical

- [ ] Pump motor voltage and amperage (for current switch sizing): _______________
- [ ] Single-phase or three-phase motor: _______________
- [ ] Motor cable OD measured (to verify current switch jaw fits): _______________
- [ ] Accessible motor lead for current switch clamp identified: _______________
- [ ] 120 VAC outlet available within 6 feet of enclosure location (or conduit run planned): _______________

### Connectivity

- [ ] WiFi available at enclosure location (SSID and signal strength noted): _______________
- [ ] WiFi credentials obtained from site owner: _______________
- [ ] Cellular as backup option (if WiFi is unreliable): yes / no
- [ ] Firewall or network restrictions that could block outbound HTTPS on port 443: _______________

### Enclosure

- [ ] Proposed enclosure mounting location identified (pump room wall, equipment pad post, other): _______________
- [ ] Mounting surface type (concrete block, wood stud, metal panel): _______________
- [ ] Distance from enclosure to farthest sensor (to size cable runs): ___ feet
- [ ] Sun exposure at enclosure location (direct sun may require ventilation or shading): _______________
- [ ] Splash zone assessment (distance from pool edge, sprinkler heads, hose bibbs): _______________

---

## Section 2: Pre-Install Preparation (Before Leaving the Shop)

- [ ] Bench acceptance test completed and all 17 tests PASSED (see bench_test_plan.md)
- [ ] `.env` file configured with correct DEVICE_ID, DEVICE_TOKEN, SUPABASE_INGEST_URL for this site
- [ ] Device registered in Supabase `devices` table with correct pool_id
- [ ] Device token hash loaded into `devices.device_token_hash`
- [ ] `device_configs` row created with site-specific threshold overrides (required_flow_gpm, P2/P3 ranges, etc.)
- [ ] WiFi credentials entered in `/etc/wpa_supplicant/wpa_supplicant.conf` or NetworkManager config on the Pi
- [ ] All cables pre-cut and labeled for the measured cable runs at this site
- [ ] Sensor transmitters verified: correct range, 1/4" NPT thread, 4-20 mA two-wire output
- [ ] Flow transmitter calibrated for this pipe's inside diameter (for clamp-on) or insertion depth set
- [ ] Loop calibrator brought to site for field verification after installation
- [ ] Camera or phone ready to photograph all wiring before enclosure is closed
- [ ] Rollback plan confirmed: if the system fails to communicate, the site will continue operating as before (read-only — no pump control is affected)

---

## Section 3: Installation Steps

### Enclosure Mounting

- [ ] Enclosure mounting location marked and confirmed with site owner
- [ ] Enclosure mounted plumb and level with stainless hardware
- [ ] All cable entry points sealed with appropriate cable glands
- [ ] DIN rail components installed in enclosure (PSU, fuse block, terminal blocks)

### Sensor Installation

- [ ] P1 transmitter installed at suction tap — threaded with PTFE tape, hand-tight plus 1.5 turns
- [ ] P2 transmitter installed at filter inlet tap
- [ ] P3 transmitter installed at filter outlet tap
- [ ] Flow transmitter installed at measured location — alignment verified per manufacturer instructions
- [ ] All transmitter cable runs routed and secured with clips or conduit
- [ ] Current switch clamped around single motor lead (not both legs of single-phase)
- [ ] Current switch trip point set above motor no-load current (verify with DMM before adjusting)

### Wiring

- [ ] All terminal blocks wired per wiring diagram (wiring_diagram.md)
- [ ] Wire labels applied at both ends of every run
- [ ] Polarity verified at each transmitter (+ and signal wires confirmed with DMM)
- [ ] Digital input wired from current switch to HAT DI-1
- [ ] All unused terminal slots capped
- [ ] Wiring photograph taken before enclosure is closed

### Power-Up

- [ ] Visual inspection of enclosure interior complete — no loose wires, no exposed conductors
- [ ] 120 VAC applied to PSU — 24 VDC verified at common bus (DMM)
- [ ] Pi powers up — LED activity confirmed
- [ ] SSH access confirmed from laptop

---

## Section 4: Post-Install Verification

### Field Calibration

- [ ] P1 channel verified at pump OFF (should read near atmospheric pressure, ~0 PSI on compound gauge or site-specific static head)
- [ ] P2 and P3 verified against existing site gauges (if present) — readings within 5% of mechanical gauges
- [ ] Flow reading compared against known pump curve at measured pressure — plausible GPM for pump model
- [ ] Pump proof verified: `pump_running = False` with pump off, `True` with pump on (check logger output)

### Logger Verification

- [ ] `sudo systemctl status spc20-logger` shows Active: running
- [ ] Logger log shows first summary cycle completing without errors
- [ ] Dispatch status is GREEN (expected for a properly operating pool)
- [ ] Data visible in Supabase `readings_1min` for this device within 2 minutes of startup

### Site Owner Briefing

- [ ] Site owner informed the device is read-only — it monitors only, it does not control anything
- [ ] Site owner provided emergency contact (Poolsure dispatch) in case RED alert is triggered
- [ ] Site owner knows not to power-cycle the enclosure without contacting Poolsure

### 24-Hour Soak

- [ ] Return to site or verify remotely after 24 hours
- [ ] No RED or unexpected YELLOW alerts during soak period
- [ ] `readings_1min` has continuous data (no gaps greater than 5 minutes)
- [ ] Upload retry mechanism confirmed working (check `uploaded` column in local SQLite)

---

## Installation Record

| Field | Value |
|-------|-------|
| Site name | |
| Pool ID (Salesforce / Supabase) | |
| Device ID | |
| Install date | |
| Installed by | |
| Enclosure location description | |
| WiFi SSID | |
| P1 transmitter model and serial | |
| P2 transmitter model and serial | |
| P3 transmitter model and serial | |
| Flow transmitter model and serial | |
| Flow meter pipe size / ID | |
| Current switch model | |
| 24-hour soak verified by | |
| 24-hour soak date | |
| Notes | |
