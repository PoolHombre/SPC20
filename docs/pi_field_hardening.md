# Raspberry Pi Field Hardening — SPC 2.0

Commercial pool equipment rooms are hot, dusty, humid, and subject to frequent power interruptions. This guide covers the steps required before a Pi is left unattended at a field site.

---

## 1. SD Card Endurance — OverlayFS

The OS filesystem runs read-only with an in-memory overlay. Only /var/lib/spc20 (persistent data) is writable on the SD card.

### Enable OverlayFS via raspi-config

```bash
sudo raspi-config
# Advanced Options → Overlay FS → Enable
# This makes / read-only at next boot
```

### Verify

```bash
sudo reboot
cat /proc/mounts | grep overlayfs
# Should show overlayfs on / type overlay ...
```

### Create a persistent data partition for spc20

Create a separate ext4 partition on the SD card for /var/lib/spc20 BEFORE enabling OverlayFS.

```bash
# Check partition layout
lsblk
# Typical: /dev/mmcblk0p1 (boot), /dev/mmcblk0p2 (rootfs)

# On a fresh image, shrink rootfs and create a 4GB data partition
# Use raspi-config to expand only to 20GB if card is 32GB, leaving 8GB for data
# Then use parted/fdisk to create /dev/mmcblk0p3 and format ext4:
sudo mkfs.ext4 /dev/mmcblk0p3
sudo mkdir -p /var/lib/spc20

# Add to /etc/fstab (before enabling OverlayFS):
echo '/dev/mmcblk0p3 /var/lib/spc20 ext4 defaults,noatime 0 2' | sudo tee -a /etc/fstab
sudo mount -a
sudo chown pi:pi /var/lib/spc20
```

Now enable OverlayFS — the data partition mounts writable; the root is read-only.

---

## 2. Log Rotation

The spc20 logger writes to journald. Prevent unbounded log growth:

```bash
# Limit journald size
sudo nano /etc/systemd/journald.conf
# Uncomment and set:
# SystemMaxUse=100M
# RuntimeMaxUse=50M
sudo systemctl restart systemd-journald
```

Or use logrotate for any file-based logs:
```bash
sudo tee /etc/logrotate.d/spc20 << 'EOF'
/var/log/spc20/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF
```

---

## 3. Hardware Watchdog Timer

The Pi's hardware watchdog reboots the device if it hangs.

```bash
# Enable in config.txt
echo 'dtparam=watchdog=on' | sudo tee -a /boot/firmware/config.txt

# Install watchdog daemon
sudo apt-get install -y watchdog

# Configure
sudo tee /etc/watchdog.conf << 'EOF'
watchdog-device = /dev/watchdog
watchdog-timeout = 15
interval = 10
max-load-1 = 24
min-memory = 1
EOF

sudo systemctl enable --now watchdog
```

Verify:
```bash
sudo systemctl status watchdog
ls -la /dev/watchdog
```

---

## 4. Automatic Service Recovery

The systemd unit already has `Restart=on-failure`. For belt-and-suspenders, set a watchdog ping from the logger service:

In spc20-logger.service (already set if `WatchdogSec=` is configured):
```ini
[Service]
WatchdogSec=120
```

The service must call `sd_notify(WATCHDOG=1)` every WatchdogSec/2 seconds. If the Python service uses systemd-notify, add:
```python
import subprocess
subprocess.run(["systemd-notify", "WATCHDOG=1"])  # call periodically in main loop
```

---

## 5. Power-Safe SQLite Configuration

Already implemented in buffer.py:
- `PRAGMA journal_mode=WAL` — write-ahead log survives power cuts
- `PRAGMA synchronous=FULL` — ensures WAL frames are durable before returning

Verify after a power cut:
```bash
sqlite3 /var/lib/spc20/spc20.db "PRAGMA integrity_check;"
# Expect: ok
```

---

## 6. Boot-Time Preflight

Create a preflight script run before the logger service starts:

```bash
sudo tee /usr/local/bin/spc20-preflight.sh << 'EOF'
#!/bin/bash
set -e
DB_PATH="${LOCAL_DB_PATH:-/var/lib/spc20/spc20.db}"

if [ -f "$DB_PATH" ]; then
  result=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
  if [ "$result" != "ok" ]; then
    logger -t spc20-preflight "INTEGRITY FAIL: $result — moving corrupt DB"
    mv "$DB_PATH" "${DB_PATH}.corrupt.$(date +%s)"
  else
    logger -t spc20-preflight "DB integrity ok"
  fi
fi
exit 0
EOF
chmod +x /usr/local/bin/spc20-preflight.sh
```

Add to spc20-logger.service:
```ini
ExecStartPre=/usr/local/bin/spc20-preflight.sh
```

---

## 7. Disable Swap

Swap on an SD card accelerates wear. Disable it:
```bash
sudo systemctl disable dphys-swapfile
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
```

---

## 8. Disable Unnecessary Services

```bash
sudo systemctl disable bluetooth
sudo systemctl disable hciuart   # if not using Bluetooth
sudo systemctl disable triggerhappy
# Disable if no display:
sudo systemctl disable raspi-config  # interactive config not needed at field
```

---

## 9. SSH Hardening

```bash
# Disable password auth — use key only
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# PermitRootLogin no
sudo systemctl restart sshd

# Ensure pi user has authorized_keys set
ls ~/.ssh/authorized_keys
```

---

## Hardening Verification Checklist

| Item | Verified |
|------|---------|
| OverlayFS active (cat /proc/mounts shows overlayfs on /) | |
| /var/lib/spc20 is on persistent partition (df shows separate mount) | |
| DB integrity_check = ok after power cut | |
| Hardware watchdog active (watchdog service running) | |
| journald size capped (SystemMaxUse=100M) | |
| Swap disabled (swapon -s shows nothing) | |
| SSH key-only auth enabled | |
| Bluetooth disabled | |
| spc20-preflight.sh runs before logger service | |
