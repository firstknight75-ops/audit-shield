# Runtime Stabilization Plan

## Objective

Turn the current repo from a strong scaffold/prototype into a runtime-validated, acceptance-driven build by executing the stack in a real Docker/Kubernetes environment, collecting failures, and fixing them in priority order.

---

## Stabilization principles

1. **No more broad feature expansion before runtime proof**
2. **Fix blockers from the bottom up**
   - infra
   - migrations
   - boot
   - workers
   - auth
   - uploads/OCR
   - analytics
   - exports
   - App Owner/admin flows
3. **Prove every security boundary in runtime**
4. **Keep evidence for every pass**
   - logs
   - commands run
   - screenshots
   - exported files
   - API responses

---

## Phase 0: Environment preparation

### Required host capabilities

- Docker
- Docker Compose
- enough RAM for:
  - postgres
  - redis
  - backend
  - celery worker
  - celery beat
  - frontend
- internet access for image/package pulls

### Verify tools

```bash
docker --version
docker compose version
```

### Repo root check

Make sure you are in the folder containing:

- `docker-compose.yml`
- `backend/`
- `scripts/`

---

## Phase 1: First boot stabilization

### Step 1: Build and start containers

```bash
docker compose up -d --build
```

### Step 2: Inspect service state

```bash
docker compose ps
```

### Expected

- postgres: running
- redis: running
- backend: running
- celery-worker: running
- celery-beat: running
- frontend: running
- baileys-bridge: running

### If any container exits

Capture:

```bash
docker compose logs <service> --tail=200
```

Priority order for inspection:

1. backend
2. postgres
3. celery-worker
4. celery-beat

---

## Phase 2: Migration stabilization

### Step 1: Run migrations explicitly

```bash
docker compose exec -T backend alembic upgrade head
```

### Expected

- no traceback
- all tables created
- RLS helper and policies applied

### Validate key tables

Run in postgres:

```bash
docker compose exec -T postgres psql -U auditcore -d auditcore -c "\dt"
```

Check for at least:

- company
- branch
- user_account
- document
- audit_ledger
- analytics_outputs
- waste_map_items
- risk_alerts
- ocr_extraction
- daily_task
- notification_queue
- inventory_client
- inventory_permission_template
- inventory_craas_request
- inventory_appowner_audit

### Validate RLS

```bash
docker compose exec -T postgres psql -U auditcore -d auditcore -c "SELECT relname, relrowsecurity FROM pg_class WHERE relname IN ('analytics_outputs','waste_map_items','risk_alerts');"
```

Expected:

- `relrowsecurity = t` for all three

---

## Phase 3: Seed stabilization

### Run seed/setup

```bash
./scripts/setup.sh
```

### Expected

- setup completes without traceback
- seeded credentials printed

### If setup fails

Capture:

- full terminal output
- `docker compose logs backend --tail=200`
- `docker compose logs postgres --tail=200`

---

## Phase 4: API boot validation

### Health

```bash
curl http://localhost:8000/health
```

Expected:

```json
{ "status": "ok", "deployment_mode": "onpremise" }
```

### Login tests

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}'
```

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}'
```

### `/auth/me`

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Stabilization goal

Confirm that:

- app boots
- auth works
- permissions resolve
- no immediate DB/session errors

---

## Phase 5: Worker and Celery stabilization

### Inspect worker logs

```bash
docker compose logs celery-worker --tail=200
```

### Inspect beat logs

```bash
docker compose logs celery-beat --tail=200
```

### Expected

- task modules imported successfully
- no broker connection failures
- no task registration errors

### Likely breakpoints to fix

- missing Celery imports
- Redis broker URL issues
- task name mismatch
- OCR dependency errors

---

## Phase 6: Upload/OCR stabilization

### Test upload

Use API flows from `API_TESTS.md`.

### Minimum validation set

1. valid JSON upload
2. valid JPG upload
3. valid PDF upload
4. fake renamed file rejection

### Observe logs

```bash
docker compose logs backend --tail=200
```

```bash
docker compose logs celery-worker --tail=200
```

### Expected

- upload returns success
- OCR task queued
- worker processes document
- no Tesseract/poppler/import errors

### If OCR fails

Typical causes:

- missing `tesseract-ocr-ara`
- missing poppler tools
- Pillow/pdf2image runtime issue
- file path or decryption bug

---

## Phase 7: Certification and ledger stabilization

### Validate certification flow

1. `GET /api/certification/next`
2. `POST /api/certification/{id}/certify`

### Validate chain

```bash
curl http://localhost:8000/api/owner/ledger/verify \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

### Tamper test

```bash
curl -X POST http://localhost:8000/api/owner/ledger/tamper/<ENTRY_ID> \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Then verify again.

### Stabilization goal

Prove:

- certification writes ledger entries
- task status changes write ledger entries
- verify endpoint detects tampering exactly

---

## Phase 8: Security-boundary stabilization

### Auditor analytics boundary

Run:

- owner dashboard endpoint as owner
- same endpoint as auditor

Expected:

- owner: success
- auditor: 403

### Database RLS verification

```bash
docker compose exec -T postgres psql -U auditcore -d auditcore -c "SELECT set_config('app.current_user_role', 'auditor', true); SELECT * FROM analytics_outputs;"
```

Expected:

- zero rows

### Manager scope validation

- login as manager
- call manager dashboard
- verify only branch-linked findings appear

### App Owner boundary validation

- login as appowner
- verify inventory endpoints work
- verify no tenant financial analytics endpoints are accessible

---

## Phase 9: Analytics stabilization

### Trigger analysis

```bash
curl -X POST http://localhost:8000/api/analytics/run/<COMPANY_ID> \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

### Validate outputs

- owner dashboard
- layer 2
- layer 3
- layer 4

### Expected

- duplicate invoice flagged
- procurement/inventory mismatch flagged
- waste map populated with IQD values
- narrative generated
- prediction generated

### If results are missing

Inspect:

- seeded invoice count
- OCR certification state
- analytics output rows
- orchestrator logs

---

## Phase 10: Export stabilization

### Test outputs first

Run exports for:

- waste map → Excel
- waste map → PDF
- waste map → PNG
- what-if → PDF

### Validate manually

- XLSX opens in Excel/LibreOffice with RTL readability
- PDF renders Arabic text correctly
- PNG is readable and suitable for sharing
- certificate fields exist

### Stabilization goal

Convert export engine from “generated file exists” to “business-usable artifact verified”.

---

## Phase 11: App Owner panel stabilization

### Validate inventory-only flows

- `/api/appowner/clients`
- `/api/appowner/clients/health-scan`
- `/api/appowner/templates/presets`
- `/api/appowner/templates`
- `/api/appowner/templates/{id}/push`
- `/api/appowner/templates/{id}/rollback`
- `/api/appowner/craas`
- `/api/appowner/maintenance`

### Tier upgrade path

Run:

```bash
./scripts/migrate-tenant-to-elite.sh <CLIENT_ID>
```

### Stabilization goal

- confirm App Owner workflows operate entirely from inventory/control-plane data
- confirm no accidental joins into tenant financial data paths

---

## Phase 12: Cloud-mode stabilization

### Deploy cloud scaffold

```bash
./scripts/deploy-cloud.sh tenant-a essential tenant_a
./scripts/deploy-cloud.sh tenant-b elite dedicated_db_placeholder
```

### Validate

- owner login
- cross-tenant isolation
- health endpoint
- inventory registration presence
- analytics trigger per tenant

### Focus

Cloud mode should be tested separately from on-prem mode because the failure classes differ.

---

## Phase 13: Failure-class triage map

### If backend fails at import time

Check:

- Python syntax errors
- missing packages
- bad imports
- circular imports

### If backend fails on startup

Check:

- FastAPI route imports
- env/config parsing
- DB engine creation

### If backend fails on DB connection

Check:

- postgres container health
- `DATABASE_URL`
- network alias names
- auth credentials

### If migrations fail

Check:

- Alembic env async config
- PostgreSQL enum/table/schema creation errors
- existing partial schema state

### If Celery fails

Check:

- Redis connectivity
- task imports
- broker/backend URLs

### If OCR fails

Check:

- Tesseract availability
- Arabic language pack
- poppler
- PIL/pdf2image exceptions

### If analytics fail

Check:

- enough certified documents
- seeded data correctness
- pandas/sklearn imports
- AI module exceptions

### If exports fail

Check:

- openpyxl
- weasyprint deps
- pillow
- filesystem write paths

---

## Phase 14: Evidence collection format

For each bug, capture:

```text
Mode: onpremise/cloud
Command run:
Observed behavior:
Expected behavior:
Service logs:
API response / traceback:
Files generated (if any):
```

This makes fixes faster and reduces guesswork.

---

## Final stabilization exit criteria

The repo is considered stabilized only when:

- [ ] stack boots cleanly
- [ ] migrations run cleanly
- [ ] setup/deploy scripts complete cleanly
- [ ] auth works for all seeded users
- [ ] OCR/certification works end-to-end
- [ ] ledger verify/tamper flows pass
- [ ] auditor boundary proven
- [ ] manager scope proven
- [ ] owner analytics proven
- [ ] App Owner control-plane proven isolated
- [ ] exports manually verified usable
- [ ] on-prem + cloud both pass their core scenarios

---

## Recommended immediate execution order

1. `docker compose up -d --build`
2. `docker compose ps`
3. `docker compose logs backend --tail=200`
4. `docker compose exec -T backend alembic upgrade head`
5. `./scripts/setup.sh`
6. auth API tests
7. upload/OCR tests
8. certification/ledger tests
9. analytics tests
10. export tests
11. App Owner tests
12. cloud deploy tests
