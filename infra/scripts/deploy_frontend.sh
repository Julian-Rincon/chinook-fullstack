#!/usr/bin/env bash
set -euo pipefail

WEB_ROOT="/var/www/chinook"
SOURCE_DIR="/tmp/chinook/frontend-dist"
NGINX_SITE="/etc/nginx/sites-available/chinook.conf"
NGINX_TEMPLATE="/tmp/chinook/infra/nginx/chinook.conf"
SERVER_NAME="${SERVER_NAME:-_}"
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo."
  exit 1
fi

if [[ -z "${BACKEND_UPSTREAM}" ]]; then
  echo "Missing BACKEND_UPSTREAM. Example: http://10.0.2.15:8000"
  exit 1
fi

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Missing staged frontend dist directory: ${SOURCE_DIR}"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/index.html" ]]; then
  echo "Missing staged frontend entry file: ${SOURCE_DIR}/index.html"
  exit 1
fi

if [[ ! -f "${NGINX_TEMPLATE}" ]]; then
  echo "Missing staged Nginx template: ${NGINX_TEMPLATE}"
  exit 1
fi

# Publish the built frontend files into the fixed Nginx web root.
mkdir -p "${WEB_ROOT}"
rsync -az --delete "${SOURCE_DIR}/" "${WEB_ROOT}/"
chown -R www-data:www-data "${WEB_ROOT}"

# Render the Nginx template with the frontend hostname and backend private URL.
sed \
  -e "s|__SERVER_NAME__|${SERVER_NAME}|g" \
  -e "s|__BACKEND_UPSTREAM__|${BACKEND_UPSTREAM}|g" \
  "${NGINX_TEMPLATE}" > "${NGINX_SITE}"

ln -sfn "${NGINX_SITE}" /etc/nginx/sites-enabled/chinook.conf
rm -f /etc/nginx/sites-enabled/default

# Validate Nginx config before reloading, then reload the running service.
nginx -t
systemctl enable nginx
systemctl reload nginx

# Verify the deployed frontend has the expected entry file in the live path.
if [[ ! -f "${WEB_ROOT}/index.html" ]]; then
  echo "Frontend deployment failed: ${WEB_ROOT}/index.html was not found after sync"
  exit 1
fi
