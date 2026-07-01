# ADR-0005: One Codebase, Two Deployment Modes (Factory Pattern)

## Status

Accepted · 2026-06-29

## Context

AuditCore runs as:

- **On-Premise Smart Box** — one physical appliance per company_group
- **Cloud** — multi-tenant SaaS with shared or dedicated databases

The two modes must:

- Share 100% of business logic, AI, OCR, ledger, permissions
- Differ ONLY in: storage backend, notification gateway, encryption key source, backup target

## Decision

We use a **factory/registry pattern** keyed on `DEPLOYMENT_MODE` (env var).

```python
# backend/app/core/factories.py
REGISTRY = {
    'onpremise': {
        'key_backend': OnPremiseKeyBackend,           # derives from COMPANY_MASTER_KEY + file UUID
        'notification_gateway': BaileysGateway,       # QR auth, Redis-queued offline retry
        'backup_target': LocalDiskBackup,
    },
    'cloud': {
        'key_backend': VaultKeyBackend,              # per-tenant DEK from Vault
        'notification_gateway': WhatsAppCloudGateway,
        'backup_target': ObjectStorageBackup,
    },
}
```

Code that needs a backend asks the factory — never inlines `if deployment_mode == 'cloud'`.

## Rationale

- Single codebase = single CI pipeline, single test suite
- New modes (hybrid, air-gapped) added by extending the registry
- All paths through business logic are tested uniformly
- `DEPLOYMENT_MODE` is read ONCE at startup, never scattered `if` checks

## Consequences

- **+** A new deployment mode is a one-file change in `core/factories.py`
- **+** Tests can swap backends via the registry without real infra
- **+** Phase 1 acceptance #1 verifies the factory pattern is the only path
- **−** Any module that bypasses the factory and reads `settings.deployment_mode`
  directly is a regression — code review must catch this

## Verification

- `backend/app/core/factories.py` — registry implementation
- `backend/app/services/encryption.py` — uses `get_key_backend()`
- `backend/app/services/notifications.py` — uses `get_notification_gateway()`
- `backend/app/tests/test_phase1_acceptance.py::test_acceptance_4_factory_supports_schema_per_tenant_and_dedicated_db`
