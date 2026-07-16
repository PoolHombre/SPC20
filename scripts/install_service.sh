#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR=/opt/spc20
SERVICE_FILE=/etc/systemd/system/spc20-logger.service

echo "Installing SPC 2.0 logger to $INSTALL_DIR"

sudo mkdir -p "$INSTALL_DIR"
sudo cp -r src "$INSTALL_DIR/"
sudo cp pyproject.toml "$INSTALL_DIR/"

if [ -f .env ]; then
  sudo cp .env "$INSTALL_DIR/.env"
  echo "Copied .env"
else
  echo "WARNING: No .env file found — copy .env.example to $INSTALL_DIR/.env and fill in values."
fi

cd "$INSTALL_DIR"
sudo python3 -m venv venv
sudo venv/bin/pip install -e .

sudo cp "$(dirname "$0")/../systemd/spc20-logger.service" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable spc20-logger
sudo systemctl start spc20-logger

echo "Done. Status:"
sudo systemctl status spc20-logger --no-pager
