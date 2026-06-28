# Backend Notes

## Core modules
- `app/api/` HTTP endpoints
- `app/services/` encryption, OCR, ledger, permissions
- `app/workers/` Celery tasks
- `app/db/` session and seeding
- `alembic/` migrations

## Key architecture rules
- Auditor analytics restriction must be enforced at PostgreSQL level.
- OCR results are not accepted without human certification.
- Ledger is append-only in workflow terms.
- Deployment mode switches via `DEPLOYMENT_MODE` only.
