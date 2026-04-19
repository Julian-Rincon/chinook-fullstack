#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE_TAG="v1.4.5"
ASSET_NAME="Chinook_PostgreSql.sql"
OUTPUT_FILE="${SCRIPT_DIR}/chinook_postgresql.sql"
DOWNLOAD_URL="https://github.com/lerocha/chinook-database/releases/download/${RELEASE_TAG}/${ASSET_NAME}"

# Download the PostgreSQL Chinook script from a pinned official release asset.
# The version is fixed so the academic setup stays reproducible over time.
curl -fL "${DOWNLOAD_URL}" -o "${OUTPUT_FILE}"

# Basic validation to fail early if the download did not return the expected SQL.
if ! grep -qi "chinook database" "${OUTPUT_FILE}"; then
  echo "Downloaded file does not look like the expected Chinook PostgreSQL SQL script."
  exit 1
fi

echo "Downloaded ${ASSET_NAME} from ${RELEASE_TAG} to ${OUTPUT_FILE}"
