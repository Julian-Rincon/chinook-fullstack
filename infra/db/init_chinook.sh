#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHINOOK_SQL_FILE="${SCRIPT_DIR}/chinook_postgresql.sql"
APP_USER_FILE="${SCRIPT_DIR}/app_user.sql"

required_vars=(DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD)

for name in "${required_vars[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}"
    exit 1
  fi
done

for path in "${CHINOOK_SQL_FILE}" "${APP_USER_FILE}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing SQL file: ${path}"
    exit 1
  fi
done

# Fail loudly if the downloaded file is still a stub or empty.
if ! grep -qi "chinook database" "${CHINOOK_SQL_FILE}"; then
  echo "The file ${CHINOOK_SQL_FILE} does not look like the Chinook PostgreSQL SQL script."
  exit 1
fi

export PGPASSWORD="${DB_PASSWORD}"

PSQL_BASE=(
  psql
  --host="${DB_HOST}"
  --port="${DB_PORT}"
  --username="${DB_USER}"
  --dbname="${DB_NAME}"
  --set=ON_ERROR_STOP=1
)

# Load the complete Chinook PostgreSQL script first so the business tables exist
# for search, customer lookup, and purchase flows.
echo "Applying Chinook PostgreSQL script..."
"${PSQL_BASE[@]}" --file="${CHINOOK_SQL_FILE}"

echo "Applying application-specific app_user table..."
"${PSQL_BASE[@]}" --file="${APP_USER_FILE}"

echo "Database initialization completed successfully."
