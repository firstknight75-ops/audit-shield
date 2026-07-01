# DEPLOYMENT.md

## On-Premise Deployment

### Overview

On-premise mode runs one Smart Box per company with no multi-tenant application complexity.

### Services

- PostgreSQL 15
- Redis 7
- FastAPI backend
- React frontend
- baileys-bridge
- Celery worker
- Celery beat

### Required environment

```bash
export DEPLOYMENT_MODE=onpremise
```

### Start

```bash
./scripts/setup.sh
```

### Verify stack

```bash
curl http://localhost:8000/health
```

Expected:

```json
{ "status": "ok", "deployment_mode": "onpremise" }
```

### Seeded credentials

```text
owner@auditcore.local    / Owner123!
gm@auditcore.local       / Gm123!
manager@auditcore.local  / Manager123!
auditor@auditcore.local  / Auditor123!
sysadmin@auditcore.local / Sysadmin123!
appowner@auditcore.local / Appowner123!
```

### On-prem operational notes

- one database per company appliance
- no shared-tenant logic needed
- file keys derived from company key + file UUID
- decrypted OCR data should stay in memory only

---

## Cloud Deployment

### Overview

Cloud mode uses the same codebase with `DEPLOYMENT_MODE=cloud`.

### Required environment

```bash
export DEPLOYMENT_MODE=cloud
```

### Cloud service expectations

- managed PostgreSQL
- managed Redis
- FastAPI backend image
- React frontend image
- whatsapp-cloud-gateway
- Vault
- Celery worker
- Celery beat

### Kubernetes manifests

Apply:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/vault.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/whatsapp-cloud-gateway.yaml
```

### Tenant provisioning

#### Essential / Advanced

- one Postgres schema per tenant in shared cluster
- set `tenant_schema`
- set session `search_path`
- keep RLS active within tenant schema

#### Elite

- dedicated database per tenant
- separate connection string provisioned at onboarding
- physical isolation path

### Cloud provisioning script

```bash
./scripts/deploy-cloud.sh tenant-a essential tenant_a
./scripts/deploy-cloud.sh tenant-b elite dedicated_db_placeholder
```

### Health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{ "status": "ok", "deployment_mode": "cloud" }
```

---

## Configuration Model

Mode switching must happen only through:

```bash
DEPLOYMENT_MODE=onpremise
```

or

```bash
DEPLOYMENT_MODE=cloud
```

Selected through factory pattern in backend:

- `get_key_backend()`
- `get_notification_gateway()`
- `get_backup_target()`

No mode-forked codebase is allowed.

---

## Database & Migration Operations

### Run migrations inside backend container

```bash
docker compose exec -T backend alembic upgrade head
```

### Seed data inside backend container

```bash
docker compose exec -T backend python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker; from app.core.config import get_settings; from app.db.seed import seed; settings=get_settings(); engine=create_async_engine(settings.database_url); Session=async_sessionmaker(engine, expire_on_commit=False); async def main():\n async with Session() as s:\n  await seed(s, deployment_mode=settings.deployment_mode);\nasyncio.run(main())"
```

---

## Post-Deployment Verification

### 1. Auth

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}'
```

### 2. Auditor RLS boundary

Run in Postgres:

```sql
SELECT set_config('app.current_user_role', 'auditor', true);
SELECT * FROM analytics_outputs;
```

Expected:

- zero rows

Run as owner:

```sql
SELECT set_config('app.current_user_role', 'owner', true);
SELECT * FROM analytics_outputs;
```

Expected:

- normal rows

### 3. OCR / Certification

- upload a valid image/PDF/JSON
- verify OCR queueing
- verify certification requires correction of yellow/red fields

### 4. Ledger integrity

```bash
curl http://localhost:8000/api/owner/ledger/verify \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

### 5. SLA engine

- confirm Celery beat running
- confirm demerit sweep every 15 minutes

---

## Container Operations

### Start stack

```bash
docker compose up -d
```

### Rebuild backend

```bash
docker compose build backend
```

### Restart backend

```bash
docker compose restart backend
```

### View logs

```bash
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f celery-beat
docker compose logs -f postgres
```

### Stop stack

```bash
docker compose down
```

---

## Kubernetes Operations

### Check pods

```bash
kubectl get pods -n auditcore
```

### Check services

```bash
kubectl get svc -n auditcore
```

### Backend logs

```bash
kubectl logs deployment/auditcore-backend -n auditcore
```

### Vault logs

```bash
kubectl logs deployment/vault -n auditcore
```

---

## Secrets & Key Handling

### On-premise

- company master key configured locally
- per-file key derived from company key + file UUID
- raw key not stored in DB

### Cloud

- key backend selected through Vault path
- tenant data encryption key fetched at request time
- should not be logged
- should not be cached to disk

---

## Backup / Restore Notes

### On-premise

- local-disk backup target selected by factory
- verify encrypted file persistence and DB dumps

### Cloud

- object-storage backup target selected by factory
- tenant DB/schema backups must be isolated per tenant

---

## Troubleshooting

### Backend not starting

- verify database is reachable
- verify Redis is reachable
- verify `DATABASE_URL`
- verify migration state

### OCR not processing

- verify Celery worker is running
- verify Redis broker connectivity
- verify Tesseract/pdf2image dependencies in runtime image

### Auditor sees analytics unexpectedly

- verify RLS enabled
- verify `set_config('app.current_user_role', ...)`
- verify hidden tables policies still exist

### Ledger verification fails

- check tampered entry id from `/api/owner/ledger/verify`
- inspect previous hash / stored hash chain

### Cloud tenant bleed risk

- verify `search_path` is set correctly
- verify tenant schema/db assignment
- verify App Owner only uses inventory schema path

---

## Recommended production hardening

- externalize all secrets
- replace placeholder/dev Vault settings
- add managed ingress/TLS
- add persistent volumes and backup policies
- add real observability and alerts
- run live integration tests after each deployment

## Phase 4 operational scripts

```bash
./scripts/install.sh
./scripts/backup.sh
./scripts/healthcheck.sh
./scripts/update.sh
```

## Phase 4 cloud tenant upgrade

```bash
./scripts/migrate-tenant-to-elite.sh <CLIENT_ID>
```
