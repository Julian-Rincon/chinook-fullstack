#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/chinook/backend"
ENV_FILE="/etc/chinook/backend.env"
SOURCE_DIR="/tmp/chinook/backend"
UNIT_SOURCE="/tmp/chinook/infra/systemd/chinook-backend.service"
UNIT_TARGET="/etc/systemd/system/chinook-backend.service"
VENV_DIR="${APP_ROOT}/.venv"
HEALTH_URL="http://127.0.0.1:8000/health"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo."
  exit 1
fi

# Validate the staged deployment files before changing the live backend path.
if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Missing staged backend source directory: ${SOURCE_DIR}"
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing backend environment file: ${ENV_FILE}"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/requirements.txt" ]]; then
  echo "Missing backend requirements file in staged source: ${SOURCE_DIR}/requirements.txt"
  exit 1
fi

if [[ ! -f "${UNIT_SOURCE}" ]]; then
  echo "Missing staged systemd unit file: ${UNIT_SOURCE}"
  exit 1
fi

# Sync the staged backend application into the fixed live path expected by the
# systemd service.
mkdir -p "${APP_ROOT}"
rsync -az --delete "${SOURCE_DIR}/" "${APP_ROOT}/"

# Create the virtual environment the first time, then reuse it on later deploys.
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  python3.12 -m venv "${VENV_DIR}"
fi

# Install or refresh Python dependencies inside the project virtual environment.
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${APP_ROOT}/requirements.txt"

# Reinstall the repo-managed service file so server state stays aligned with
# version-controlled infrastructure.
install -m 644 "${UNIT_SOURCE}" "${UNIT_TARGET}"
chown -R www-data:www-data /opt/chinook

# Reload systemd, restart the API, and fail immediately if the service is not
# healthy after restart.
systemctl daemon-reload
systemctl enable chinook-backend
systemctl restart chinook-backend
systemctl --no-pager --full status chinook-backend

# Run a simple application health check against the backend service itself.
curl -fsS "${HEALTH_URL}"
