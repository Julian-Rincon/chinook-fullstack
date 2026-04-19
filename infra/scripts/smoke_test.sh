#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1}"
HEALTH_PATH="${2:-/health}"

# Keep the path explicit so the same helper can validate:
# - backend direct health checks on /health
# - frontend public checks on /api/health
curl -fsS "${BASE_URL}${HEALTH_PATH}"
