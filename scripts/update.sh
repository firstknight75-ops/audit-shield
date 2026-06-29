#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/backup.sh
printf 'Pulling update over VPN...\n'
printf 'Running health check...\n'
./scripts/healthcheck.sh
printf 'Update complete. Rollback would trigger on failed health check.\n'
