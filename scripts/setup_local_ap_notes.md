# Local AP Setup — nmcli Step-by-Step

## Prerequisites

- Raspberry Pi OS Bookworm (64-bit)
- NetworkManager installed and active: `sudo systemctl status NetworkManager`
- `wlan0` visible: `ip link show wlan0`
- Device label showing DEVICE_ID and DEVICE_TOKEN

## Variables (set these before running commands)

```bash
DEVICE_ID="spc20-b1-bench-0001"
# SSID suffix = last 4 chars of DEVICE_ID
AP_SSID="SPC-20-POC-0001"
# Password = first 16 chars of DEVICE_TOKEN (from device label)
AP_PSK="replace16charhere"
AP_IP="192.168.99.1/24"
```

## Step 1 — Confirm NetworkManager owns wlan0

```bash
nmcli general status
nmcli device status | grep wlan0
```

Expected: `wlan0   wifi   connected   <ssid>` or `disconnected`.

If `unmanaged`, add to NetworkManager:
```bash
sudo nmcli device set wlan0 managed yes
```

## Step 2 — Remove conflicting services

```bash
# Disable hostapd if present (conflicts with NM AP mode)
sudo systemctl stop hostapd 2>/dev/null
sudo systemctl disable hostapd 2>/dev/null
# Disable dhcpcd if present
sudo systemctl stop dhcpcd 2>/dev/null
sudo systemctl disable dhcpcd 2>/dev/null
```

## Step 3 — Create the AP profile

```bash
sudo nmcli connection add \
  type wifi \
  ifname wlan0 \
  con-name spc20-ap \
  ssid "${AP_SSID}" \
  mode ap \
  band bg \
  channel 6 \
  ipv4.method shared \
  ipv4.addresses "${AP_IP}" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "${AP_PSK}" \
  connection.autoconnect no
```

Verify:
```bash
nmcli connection show spc20-ap
```

## Step 4 — Test the AP profile

Disconnect from upstream first (so wlan0 is free):
```bash
# Optional: bring down site wifi to simulate fallback
sudo nmcli connection down site-wifi 2>/dev/null
sudo nmcli connection up spc20-ap
nmcli connection show --active
iw wlan0 info | grep type
# Expect: type: AP
```

From a phone or laptop:
1. Scan for `SPC-20-POC-0001`
2. Enter the AP password (first 16 chars of DEVICE_TOKEN)
3. Open `http://192.168.99.1:8080`

## Step 5 — Configure site Wi-Fi via SSH (when connected through AP)

```bash
ssh pi@192.168.99.1
SITE_SSID="PoolsureHQ"
SITE_PSK="sitepassword"

sudo nmcli connection add \
  type wifi \
  ifname wlan0 \
  con-name site-wifi \
  ssid "${SITE_SSID}" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "${SITE_PSK}" \
  connection.autoconnect yes \
  connection.autoconnect-priority 100
```

## Step 6 — Revert to client mode

```bash
sudo nmcli connection down spc20-ap
sudo nmcli connection up site-wifi
# Verify upstream
ping -c 3 8.8.8.8
```

## Step 7 — Enable watchdog (automates fallback)

```bash
sudo systemctl enable spc20-network-watchdog.service
sudo systemctl start spc20-network-watchdog.service
journalctl -u spc20-network-watchdog -f
```

## Persistent AP profile check

The profile should survive reboots:
```bash
sudo reboot
# After reboot, with no upstream:
nmcli connection show --active
# Should show spc20-ap active (started by watchdog)
```

## Troubleshooting

```bash
# Full NM debug log
sudo journalctl -u NetworkManager --since "5 min ago"

# Test ping through AP to verify routing
# From connected client:
ping 192.168.99.1

# Check DHCP is working on AP
ip addr show wlan0
# Should show 192.168.99.1 or assigned client IP

# Force AP deactivation if stuck
sudo nmcli connection down spc20-ap
sudo nmcli connection up site-wifi
```
