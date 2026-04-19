#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/chinook/backend"
ENV_DIR="/etc/chinook"
ENV_FILE="${ENV_DIR}/backend.env"
UNIT_TARGET="/etc/systemd/system/chinook-backend.service"
UNIT_SOURCE="/tmp/chinook/infra/systemd/chinook-backend.service"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo."
  exit 1
fi

# This script prepares a fresh Ubuntu EC2 instance to host the FastAPI backend.
# It is safe to re-run: packages are re-checked, directories are recreated if
# missing, and the systemd unit is reinstalled from the repo-managed file.

# Install the system packages required to run a Python 3.12 FastAPI service,
# deploy code with rsync, and initialize PostgreSQL from the backend host.
# `postgresql-client` provides the `psql` command used by infra/db/init_chinook.sh.
apt-get update
apt-get install -y software-properties-common curl rsync build-essential libpq-dev postgresql-client

# Ubuntu 24.04 already includes Python 3.12. On older images this adds the PPA
# only if python3.12 is not yet available.
if ! command -v python3.12 >/dev/null 2>&1; then
  add-apt-repository -y ppa:deadsnakes/ppa
  apt-get update
fi

apt-get install -y python3.12 python3.12-venv python3-pip

# Create the fixed deployment directories expected by the repo scripts and
# systemd service.
mkdir -p "${APP_ROOT}" "${ENV_DIR}"
install -d -m 755 -o www-data -g www-data /opt/chinook
install -d -m 755 -o www-data -g www-data "${APP_ROOT}"
install -d -m 750 "${ENV_DIR}"

# Create the environment file with secure permissions if it does not already
# exist. The file is intentionally left without credentials.
if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 600 /dev/null "${ENV_FILE}"
fi

# Install the dedicated backend unit from the repository so the server does not
# depend on any manually created /usr/local/bin files.
install -m 644 "${UNIT_SOURCE}" "${UNIT_TARGET}"
chown -R www-data:www-data /opt/chinook
chown root:root "${UNIT_TARGET}" "${ENV_FILE}"
chmod 600 "${ENV_FILE}"

systemctl daemon-reload
systemctl enable chinook-backend

# Do not force-start the service during bootstrap because the application code
# and final backend.env values may not be deployed yet. If a previous failed
# service exists, clear the failed state to keep the machine clean.
systemctl reset-failed chinook-backend >/dev/null 2>&1 || true

echo "Backend server bootstrap completed."
echo "Next steps:"
echo "1. Deploy code with infra/scripts/deploy_backend.sh"
echo "2. Populate /etc/chinook/backend.env with real values"
echo "3. Start the service after deployment with: sudo systemctl restart chinook-backend"
