#!/usr/bin/env bash
set -euo pipefail

WEB_ROOT="/var/www/chinook"
NGINX_SITE="/etc/nginx/sites-available/chinook.conf"
NGINX_LINK="/etc/nginx/sites-enabled/chinook.conf"
NGINX_TEMPLATE="/tmp/chinook/infra/nginx/chinook.conf"
SERVER_NAME="${SERVER_NAME:-_}"
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-http://127.0.0.1:8000}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo."
  exit 1
fi

# This script prepares a fresh Ubuntu EC2 instance to host the React build and
# reverse proxy /api requests to the backend EC2 private address. It is safe to
# re-run: packages are rechecked, directories are recreated if missing, and the
# Nginx site file is refreshed from the repository template.
apt-get update
apt-get install -y nginx rsync curl

# Create the static site directory and Nginx site directories with safe
# ownership for files that will later be published by the deploy script.
mkdir -p "${WEB_ROOT}" /etc/nginx/sites-available /etc/nginx/sites-enabled
chown -R www-data:www-data "${WEB_ROOT}"

# Install a rendered site config from the repo-managed template. The bootstrap
# defaults are intentionally generic; the frontend deploy script will render the
# final config again using the real backend private address and hostname.
sed \
  -e "s|__SERVER_NAME__|${SERVER_NAME}|g" \
  -e "s|__BACKEND_UPSTREAM__|${BACKEND_UPSTREAM}|g" \
  "${NGINX_TEMPLATE}" > "${NGINX_SITE}"

ln -sfn "${NGINX_SITE}" "${NGINX_LINK}"
if [[ -L /etc/nginx/sites-enabled/default || -f /etc/nginx/sites-enabled/default ]]; then
  rm -f /etc/nginx/sites-enabled/default
fi

# Validate the configuration before touching the running Nginx process.
nginx -t
systemctl enable nginx
if systemctl is-active --quiet nginx; then
  systemctl reload nginx
else
  systemctl restart nginx
fi

echo "Frontend server bootstrap completed."
echo "Next steps:"
echo "1. Deploy the frontend build with infra/scripts/deploy_frontend.sh"
echo "2. Pass SERVER_NAME and BACKEND_UPSTREAM when running the deploy script"
