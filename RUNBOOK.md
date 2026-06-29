# AuditCore — Operator Runbook

## Common Operations

### Health check
```bash
curl http://localhost:8000/health
# {"status":"ok","deployment_mode":"onpremise"}

curl http://localhost:8000/ready
# {"status":"ok","database":"ok","redis":"ok"}

curl http://localhost:8000/metrics | head -50
# Prometheus metrics
```

### Manual daily analysis trigger
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}' | jq -r .access_token)

COMPANY_ID=$(curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq -r '.accessible_companies[0].company_id')

curl -X POST "http://localhost:8000/api/analytics/run/${COMPANY_ID}" \
  -H "Authorization: Bearer $TOKEN"
```

### Verify ledger integrity
```bash
curl "http://localhost:8000/api/owner/ledger/verify?company_id=${COMPANY_ID}" \
  -H "Authorization: Bearer $TOKEN"
# { "valid": true, "message": "... سليم 100%", "broken_entry_id": null }
```

### Trigger tamper test (proves detection works)
```bash
# Pick a recent ledger entry
ENTRY_ID=$(...)

# "Tamper" with it (test-only)
curl -X POST "http://localhost:8000/api/owner/ledger/tamper/${ENTRY_ID}?company_id=${COMPANY_ID}" \
  -H "Authorization: Bearer $TOKEN"

# Verify should now return broken_entry_id
curl "http://localhost:8000/api/owner/ledger/verify?company_id=${COMPANY_ID}" \
  -H "Authorization: Bearer $TOKEN"
```

### Add a reverse entry (production correction)
```bash
curl -X POST "http://localhost:8000/api/owner/ledger/reverse/${ENTRY_ID}?company_id=${COMPANY_ID}" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"reason":"Corrected vendor name","correction":{"vendor_name":"الرافدين"}}'
```

### Schedule a recurring report
```bash
curl -X POST "http://localhost:8000/api/scheduled-reports" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"report_type":"trust_index","format":"pdf","cron":"daily 07:00","recipients":["owner@example.com"]}'
```

## Incident Response

### Suspected Auditor access to analytics
1. Check the Trust Center `/trust` page — denied-attempt counter should show
   the actual blocked queries
2. Verify the migration is applied: `alembic current` should show 0001 applied
3. Verify session context is set: inspect `/api/trust-proof/run` output
4. If violations are real, audit `/api/admin/activity` for permission changes

### Ledger chain breaks
1. Run `verify` — get the exact `broken_entry_id`
2. Inspect that entry's `action_payload` for the mutation
3. **Do not edit the row directly.** Add a `reverse_entry` instead.
4. If the cause is corruption (disk failure, etc.), restore from the
   most recent atomic backup (`scripts/backup.sh` output)

### Worker not processing OCR
1. Check Celery worker logs: `docker logs auditcore-celery-worker-1`
2. Inspect Redis: `docker exec -it auditcore-redis-1 redis-cli LLEN ocr`
3. Verify Tesseract is installed: `docker exec auditcore-backend tesseract --version`
4. Re-run a single document: `curl -X POST /api/admin/celery/reprocess/{doc_id}`

### 48-hour activation missed
1. Inspect `/api/owner/activation-progress` — which stage stalled?
2. App Owner dashboard `/appowner/overdue-installs` shows the install flagged
3. Resolve and re-run the missing step manually
4. The shareable completion banner appears once stage 4 lands

## Backup / Restore

### On-premise backup (atomic per company_group)
```bash
./scripts/backup.sh
# Creates: backups/backup-<stamp>.enc — one file per company_group
```

### Restore from backup
```bash
# Stop services first
docker compose down

# Restore
./scripts/restore.sh backups/backup-20260629-120000.enc

# Re-start
docker compose up -d
```

### Cloud snapshot
Cloud mode uses automated snapshot backups + a downloadable
encrypted export bundle per tenant. See `DEPLOYMENT.md` § Cloud.

## Capacity Planning

| Resource | Per 10K tx/day | Scaling trigger |
|---|---|---|
| Postgres CPU | ~5% | > 30% sustained → consider read replica |
| Postgres disk | +1 GB/day | > 80% → enable partitioning |
| Redis memory | ~50 MB | > 80% → bump instance class |
| Backend CPU | ~10% per worker | > 60% → add worker pod |
| OCR throughput | 3 s/page | > 5 s/page → enable GPU tesseract |
| API p50 | < 150 ms | > 300 ms → check indexes (Phase 5 migration) |

## Migration safety

```bash
# Dry-run
alembic upgrade --sql head > migration.sql
# Inspect
less migration.sql

# Apply
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

Each migration in this repo is reversible via `downgrade()`. Phase 5
migration (`0004`) adds indexes that improve performance but are not
required for correctness.
