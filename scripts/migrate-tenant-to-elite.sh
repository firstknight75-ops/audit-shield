#!/usr/bin/env bash
set -euo pipefail
CLIENT_ID="${1:?client id required}"
cd "$(dirname "$0")/.."
printf 'Starting pooled-schema to dedicated-DB migration for client %s
' "$CLIENT_ID"
printf '1) Freeze writes
'
printf '2) Snapshot schema
'
printf '3) Provision dedicated database
'
printf '4) Copy tenant schema data
'
printf '5) Update inventory_client.dedicated_database_url and clear tenant_schema
'
printf '6) Run health checks
'
printf '7) Unfreeze writes
'
printf 'Migration scaffold complete.
'
