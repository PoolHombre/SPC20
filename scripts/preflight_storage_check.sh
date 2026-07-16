#!/usr/bin/env bash
# preflight_storage_check.sh — pre-flight checks before starting the logger.
# Exits non-zero on any critical failure.
# SECURITY: Never prints secrets, credentials, or key material.
set -euo pipefail

PASS=0
WARN=0
FAIL=0

SPC20_DATA_DIR="${SPC20_DATA_DIR:-/var/lib/spc20}"
SPC20_CONFIG_DIR="${SPC20_CONFIG_DIR:-/etc/spc20}"
ENV_FILE="$SPC20_CONFIG_DIR/spc20.env"
MIN_FREE_MB="${MIN_FREE_MB:-200}"

ok()   { echo "  [OK]   $*"; }
warn() { echo "  [WARN] $*"; WARN=$((WARN+1)); }
fail() { echo "  [FAIL] $*"; FAIL=$((FAIL+1)); }

echo "=== SPC 2.0 Pre-flight Storage Check ==="

# 1. Data directory exists and is writable
if [ -d "$SPC20_DATA_DIR" ] && [ -w "$SPC20_DATA_DIR" ]; then
    ok "Data directory exists and is writable: $SPC20_DATA_DIR"
else
    fail "Data directory missing or not writable: $SPC20_DATA_DIR"
fi

# 2. Config/env file exists (do NOT print its contents)
if [ -f "$ENV_FILE" ]; then
    ok "Environment file present: $ENV_FILE"
else
    warn "Environment file not found: $ENV_FILE — defaults will be used"
fi

# 3. Disk space check
if command -v df &>/dev/null; then
    FREE_MB=$(df -m "$SPC20_DATA_DIR" 2>/dev/null | awk 'NR==2 {print $4}')
    if [ -n "$FREE_MB" ] && [ "$FREE_MB" -lt "$MIN_FREE_MB" ]; then
        fail "Low disk space: ${FREE_MB} MB free (minimum: ${MIN_FREE_MB} MB)"
    elif [ -n "$FREE_MB" ]; then
        ok "Disk space: ${FREE_MB} MB free"
    fi
fi

# 4. tmpfs warning — SQLite WAL performs poorly on tmpfs
if command -v findmnt &>/dev/null; then
    FSTYPE=$(findmnt -no FSTYPE "$SPC20_DATA_DIR" 2>/dev/null || echo "unknown")
    if [ "$FSTYPE" = "tmpfs" ]; then
        warn "Data directory is on tmpfs — data will be lost on reboot!"
    else
        ok "Filesystem type: $FSTYPE"
    fi
fi

# 5. System time sanity — year must be >= 2025
YEAR=$(date +%Y 2>/dev/null || echo "0")
if [ "$YEAR" -lt 2025 ]; then
    fail "System clock appears wrong: year=$YEAR — timestamps will be invalid"
else
    ok "System time: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
fi

# 6. Required env vars (check existence only, never print values)
for var in DEVICE_ID DEVICE_TOKEN SUPABASE_INGEST_URL; do
    if [ -f "$ENV_FILE" ] && grep -q "^${var}=" "$ENV_FILE" 2>/dev/null; then
        ok "Config key present: $var"
    elif [ -n "${!var:-}" ]; then
        ok "Env var set: $var"
    else
        warn "Missing config: $var — logger may fail to start"
    fi
done

echo ""
echo "=== Results: OK=$PASS  WARN=$WARN  FAIL=$FAIL ==="

if [ "$FAIL" -gt 0 ]; then
    echo "Pre-flight FAILED — address failures before starting the logger."
    exit 1
fi
if [ "$WARN" -gt 0 ]; then
    echo "Pre-flight PASSED with warnings."
    exit 0
fi
echo "Pre-flight PASSED."
exit 0
