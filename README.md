# AuditCore / Audit Shield

AuditCore is a sovereign audit intelligence platform designed for the Iraqi business environment, with hard architectural boundaries for Auditor visibility and dual deployment modes from one codebase.

## Core guarantees

- **Auditor cannot read analytics output architecturally** via PostgreSQL RLS, not UI hiding.
- **Single codebase, dual deployment** via one setting:
  - `DEPLOYMENT_MODE=onpremise`
  - `DEPLOYMENT_MODE=cloud`
- **Immutable ledger**: no update/delete workflow for audit events; only append and reverse-entry patterns.
- **No OCR auto-commit**: OCR output must be human-certified before acceptance.

---

## Repository structure

- `backend/` — FastAPI, SQLAlchemy, Celery, Alembic
- `src/` — React + Vite + RTL frontend
- `baileys-bridge/` — on-prem WhatsApp bridge stub
- `k8s/` — cloud manifests
- `scripts/` — setup and validation helpers

---

## Deployment modes

### On-premise
Uses:
- Postgres 15
- Redis 7
- FastAPI backend
- React frontend
- `baileys-bridge`

Command:
```bash
./scripts/setup.sh
```

### Cloud
Uses same backend/frontend images, but cloud-selected services:
- managed Postgres
- managed Redis
- `whatsapp-cloud-gateway`
- Vault

Provision cloud resources/manifests with:
```bash
./scripts/deploy-cloud.sh tenant-name essential tenant_schema_name
```

---

## Quick start

### 1. Start on-premise stack
```bash
./scripts/setup.sh
```

### 2. Seeded accounts
```text
owner@auditcore.local    / Owner123!
gm@auditcore.local       / Gm123!
manager@auditcore.local  / Manager123!
auditor@auditcore.local  / Auditor123!
sysadmin@auditcore.local / Sysadmin123!
appowner@auditcore.local / Appowner123!
```

### 3. Health check
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok","deployment_mode":"onpremise"}
```

---

## Authentication API

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}'
```

Expected: access + refresh tokens.

### Current user
```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Expected:
- role
- effective permissions list

Acceptance target:
- each of the 6 seeded users returns a different effective permission set.

---

## Document upload / OCR certification flow

### Upload document
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F file=@sample-invoice.json
```

Accepted formats:
- `.xlsx`
- `.csv`
- `.docx`
- `.jpg`
- `.png`
- `.tiff`
- `.pdf`
- `.json`

Rules:
- max 50MB
- MIME must match extension
- renamed `.exe` as `.pdf` must be rejected
- file is encrypted at rest immediately
- OCR is queued for worker processing

### Fetch next certification item
```bash
curl http://localhost:8000/api/certification/next \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

Expected:
- oldest pending document
- extracted fields
- confidence values
- confidence color classification:
  - green >= 85
  - yellow 60-84
  - red < 60 or missing

### Certify corrected OCR
```bash
curl -X POST http://localhost:8000/api/certification/<EXTRACTION_ID>/certify \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "fields": {
      "invoice_number": "INV-2026-9001",
      "date": "2026-06-28",
      "amount": "12450000",
      "vendor_name": "شركة الرافدين",
      "items_list": ["صنف 1", "صنف 2"]
    }
  }'
```

Expected:
- success message
- next pending document payload if available
- ledger append event created
- linked task marked done

Rule:
- yellow/red fields must be corrected before certification is accepted.

---

## Auditor analytics boundary verification

Auditor must never see:
- `analytics_outputs`
- `waste_map_items`
- `risk_alerts`

### API-level expectation
Even after successful document certification, Auditor still must not access analytics endpoints/tables.

### DB-level RLS check
Run inside Postgres:
```sql
SELECT set_config('app.current_user_role', 'auditor', true);
SELECT * FROM analytics_outputs;
```
Expected:
- `0 rows`

Then:
```sql
SELECT set_config('app.current_user_role', 'owner', true);
SELECT * FROM analytics_outputs;
```
Expected:
- normal rows returned

---

## Immutable ledger verification

### Verify chain via API
```bash
curl http://localhost:8000/api/owner/ledger/verify \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected clean response:
```json
{
  "valid": true,
  "message": "السجل سليم 100%",
  "broken_entry_id": null
}
```

### Tamper test
```bash
curl -X POST http://localhost:8000/api/owner/ledger/tamper/<ENTRY_ID> \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Re-run verify:
```bash
curl http://localhost:8000/api/owner/ledger/verify \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected:
- `valid: false`
- exact broken entry id returned

---

## SLA / daily task engine

Schedules:
- daily generation at **08:00 Baghdad time**
- demerit sweep every **15 minutes**

SLAs:
- OCR: 4h
- statements: 24h
- reversals: 2h
- branch backlog: configured normal path

Demerits:
- critical: 3
- normal: 1

Efficiency formula:
```text
(on_time / total) * 100 - (demerits * 5)
```

Owner-only endpoint:
```bash
curl http://localhost:8000/api/owner/auditor-efficiency \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

---

## Validation scripts

### On-prem setup
```bash
./scripts/setup.sh
```

### Cloud tenant deploy
```bash
./scripts/deploy-cloud.sh tenant-a essential tenant_a
./scripts/deploy-cloud.sh tenant-b elite dedicated_db_placeholder
```

### Integration guidance
```bash
./scripts/run-integration-checks.sh
```

This prints the Docker-enabled validation flow to run on a machine with Docker.

---

## Test inventory

### Regression tests
```bash
pytest -q backend/app/tests/test_phase2.py backend/app/tests/test_integration_api.py
```

### Manual acceptance checklist

1. Login as Auditor
2. Upload Arabic invoice
3. Confirm encryption-at-rest
4. Wait for OCR worker
5. Fetch `/api/certification/next`
6. Correct yellow/red fields
7. Certify document
8. Verify ledger chain
9. Confirm Auditor still cannot access analytics
10. Force SLA miss and verify demerit
11. Tamper ledger entry and verify exact broken link detection

---

## Operator runbook

### On-prem runbook
1. Ensure Docker/Compose installed
2. Run `./scripts/setup.sh`
3. Verify `/health`
4. Login with seeded Owner account
5. Verify Auditor queue and ledger endpoints

### Cloud runbook
1. Apply `k8s/` manifests or use provision workflow
2. Set `DEPLOYMENT_MODE=cloud`
3. Ensure managed Postgres/Redis and Vault are reachable
4. Provision tenant schema or dedicated DB based on tier
5. Seed tenant
6. Run RLS verification inside tenant scope

---

## Security notes

- Rotate any GitHub token previously shared in chat.
- Vault-backed keys are selected only in `DEPLOYMENT_MODE=cloud`.
- On-prem keys derive from company key + file UUID; raw key is not stored in DB.
- Decrypted OCR payload should exist only in process memory.

---

## Known current gaps

This repository now contains a strong scaffold, but a production-hardening pass is still recommended for:
- full end-to-end live integration tests against running Docker services
- stronger dedicated-DB cloud provisioning for Elite tier
- fully live frontend-to-backend wiring replacing remaining mock UX pieces
- reverse-entry-only correction workflows for every ledger-sensitive business action
- real Vault secret fetch implementation instead of scaffolded key material behavior
