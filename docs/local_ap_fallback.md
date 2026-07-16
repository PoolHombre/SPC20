# Local AP Fallback — SPC 2.0

## Purpose

When the device cannot connect to the site Wi-Fi network (wrong credentials, network down, or first-time setup before credentials are known), the SPC 2.0 Pi activates a local access point (AP). The technician can connect directly to the device to configure it, retrieve logs, or access the dashboard.

## When the AP activates

The network watchdog service (`spc20-network-watchdog.service`) checks for an active upstream connection every 60 seconds. If no upstream route is detected after 90 seconds (configurable), the Pi switches `wlan0` into AP mode. It reverts to client mode as soon as a valid upstream connection is re-established.

Manual trigger: `sudo systemctl restart spc20-network-watchdog.service`

## AP Credentials

| Item | Value |
|------|-------|
| SSID | `SPC-20-POC-<last4-of-DEVICE_ID>` |
| Example | `SPC-20-POC-0001` for DEVICE_ID `spc20-b1-bench-0001` |
| Security | WPA2 (WPA3 if supported by Pi hardware) |
| Password | Device token — first 16 characters, printed on device label |
| Band | 2.4 GHz (maximum compatibility) |
| IP range | 192.168.99.1/24 (Pi is gateway) |
| Pi IP | 192.168.99.1 |
| Dashboard | http://192.168.99.1:8080 |

**Note:** The AP password is the first 16 characters of the `DEVICE_TOKEN` env var. This is set during provisioning and printed on the device label. It is not the full device token.

## Manual Pi OS Steps

These steps assume Raspberry Pi OS (Bookworm, 64-bit) and `NetworkManager` as the network manager. Do not use `dhcpcd` — it conflicts with AP mode under NetworkManager.

### 1 — Verify NetworkManager is managing wlan0

```bash
nmcli device status
# wlan0 should show 'wifi' and 'connected' or 'disconnected'
```

### 2 — Create the AP connection profile

```bash
# Replace SPC-20-POC-0001 with your device SSID
# Replace the password with first 16 chars of DEVICE_TOKEN
sudo nmcli connection add \
  type wifi \
  ifname wlan0 \
  con-name spc20-ap \
  ssid "SPC-20-POC-0001" \
  mode ap \
  band bg \
  channel 6 \
  ipv4.method shared \
  ipv4.addresses "192.168.99.1/24" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "FIRST16CHARSTOKEN" \
  connection.autoconnect no
```

### 3 — Activate AP manually (for testing)

```bash
sudo nmcli connection up spc20-ap
```

### 4 — Verify it is running

```bash
nmcli connection show --active
iw wlan0 info
# Should show type: AP
```

### 5 — Connect from technician laptop/phone

- SSID: `SPC-20-POC-0001`
- Password: first 16 characters of device token (on device label)
- Open browser: `http://192.168.99.1:8080`

### 6 — Configure site Wi-Fi while connected through AP

```bash
ssh pi@192.168.99.1
# Edit /etc/spc20/.env or use the dashboard "Network" section (not yet implemented — manual for Build 1)
sudo nmcli connection add \
  type wifi \
  ifname wlan0 \
  con-name site-wifi \
  ssid "SiteNetworkName" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "SitePassword" \
  connection.autoconnect yes
# Then deactivate AP and test client mode:
sudo nmcli connection down spc20-ap
sudo nmcli connection up site-wifi
```

### 7 — Revert AP mode after configuration

The watchdog will automatically switch back to client mode. If still in AP mode manually:

```bash
sudo nmcli connection down spc20-ap
sudo systemctl restart spc20-network-watchdog.service
```

## Security Notes

- The AP is only active when upstream is unavailable. It auto-disables.
- WPA2 with a per-device password prevents casual access.
- Dashboard behind HTTP Basic Auth — use HTTPS via stunnel or tailscale for remote access.
- The AP password (short token prefix) is not the same as the Supabase ingest token — compromise of the AP credential does not expose cloud credentials.
- Log AP activation/deactivation events to syslog: `journalctl -u spc20-network-watchdog -f`

## Troubleshooting

| Symptom | Check |
|---------|-------|
| AP not appearing | `nmcli connection show spc20-ap` — confirm profile exists |
| Can't connect to AP | Verify WPA2 password is exactly first 16 chars of token |
| Dashboard not loading | Confirm port 8080 is not firewalled: `sudo ufw status` |
| AP stuck on after upstream returns | `sudo systemctl restart spc20-network-watchdog.service` |
| wlan0 already in use | Check if `hostapd` is also running — it conflicts with NM AP mode |
