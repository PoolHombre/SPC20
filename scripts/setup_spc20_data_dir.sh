#!/usr/bin/env bash
# setup_spc20_data_dir.sh — idempotent setup of SPC 2.0 data directories.
# Safe to run multiple times.
set -euo pipefail

SPC20_DATA_DIR="${SPC20_DATA_DIR:-/var/lib/spc20}"
SPC20_CONFIG_DIR="${SPC20_CONFIG_DIR:-/etc/spc20}"
SPC20_USER="${SPC20_USER:-spc20}"
SPC20_GROUP="${SPC20_GROUP:-spc20}"

echo "==> Setting up SPC 2.0 data directories"

# Create system user/group if not present
if ! id -u "$SPC20_USER" &>/dev/null; then
    echo "  Creating system user: $SPC20_USER"
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SPC20_USER"
fi

# Create directories
for dir in "$SPC20_DATA_DIR" "$SPC20_CONFIG_DIR"; do
    if [ ! -d "$dir" ]; then
        echo "  Creating directory: $dir"
        mkdir -p "$dir"
    fi
done

# Set ownership and permissions
chown -R "$SPC20_USER:$SPC20_GROUP" "$SPC20_DATA_DIR"
chmod 750 "$SPC20_DATA_DIR"

# Config dir: root-owned, readable by spc20 group
chown root:"$SPC20_GROUP" "$SPC20_CONFIG_DIR"
chmod 750 "$SPC20_CONFIG_DIR"

# If env file exists, tighten permissions (contains credentials)
ENV_FILE="$SPC20_CONFIG_DIR/spc20.env"
if [ -f "$ENV_FILE" ]; then
    chown root:"$SPC20_GROUP" "$ENV_FILE"
    chmod 640 "$ENV_FILE"
    echo "  Secured $ENV_FILE"
fi

echo "==> Done. Data dir: $SPC20_DATA_DIR  Config dir: $SPC20_CONFIG_DIR"
