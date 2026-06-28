#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/setup.sh
printf '\nOn-prem install complete. First login should be available within 30 minutes or less.\n'
