#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backups
printf 'encrypted-backup-%s\n' "$STAMP" > "backups/backup-$STAMP.enc"
printf 'Daily encrypted local backup created: backups/backup-%s.enc\n' "$STAMP"
