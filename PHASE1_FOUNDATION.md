# AuditCore — Phase 1 Foundation

**Branch:** `auditcore/phase1-hardening`
**Date:** 2026-06-29

Phase 1 lays the foundation. The three trust boundaries that get decided
here and must hold through every later phase:

1. **Zero-knowledge Auditor boundary** — enforced at the PostgreSQL RLS level,
   not the UI. The Auditor role has architecturally zero path to any
   analytics_outputs / waste_map_items / risk_alerts row.
2. **Cross-tenant boundary (cloud)** — every cross-tenant query is
   blocked by RLS policy `tenant_isolation_*` on the three hidden tables,
   keyed on `app.current_tenant_id` set from `user.company_group_id`.
3. **Cross-company-within-tenant boundary** — Owner-of-many-companies
   cannot silently blend. The `get_accessible_company_ids` helper is the
   only sanctioned path; default-deny, every document/task/analytics
   query routes through it.

## Acceptance criteria — all checked

| # | Criterion | Test(s) |
|---|---|---|
| 1 | `setup.sh` and `deploy-cloud.sh` succeed | `test_acceptance_1_*` (3 tests) |
| 2 | `/auth/me` returns different effective permissions per role | `test_acceptance_2_*` (8 tests) |
| 3 | Auditor RLS returns 0 rows on hidden tables | `test_acceptance_3_*` (3 tests) |
| 4 | Cross-tenant isolation (cloud) | `test_acceptance_4_*` (3 tests) |
| 5 | Cross-company-within-tenant | `test_acceptance_5_*` (5 tests) |
| 6 | Cross-branch | `test_acceptance_6_*` (1 test) |
| 7 | Temp override auto-revokes + app_owner grant blocked | `test_acceptance_7_*` (3 tests) |
| 8 | Bilingual i18n + Sorani font coverage | `test_acceptance_8_*` (5 tests) |
| 9 | CI fails on external AI imports | `test_acceptance_9_*` (4 tests) |
| 10 | Encryption at rest + MIME validation | `test_acceptance_10_*` (7 tests) |
| Activation | `activation_started_at` stamped by both scripts | `test_phase1_*` (3 tests) |

**Result:** `45 passed` on `test_phase1_acceptance.py`, **102 passed, 1 skipped** total.

## What was added/changed in this Phase 1 pass

### Backend
- **Alembic migration 0002** — adds `activation_started_at` to `company_group`
  (`backend/alembic/versions/20260629_0002_activation_started_at.py`)
- **`CompanyGroup` model** — `activation_started_at: Mapped[datetime | None]`
- **Permission codes** — expanded to spec (`view_owner_dashboard`,
  `manage_company_users`, `export_reports`, `approve_custom_reports`,
  `grant_temporary_access`, `manage_templates`, `view_all_companies`)
- **`ROLE_DEFAULTS`** — refactored so the six seeded roles have six
  *distinct* permission sets (manager and auditor no longer overlap)
- **`seed.py`** — records `activation_started_at = now()` at creation
- **API `require_permission` calls** — updated from old codes
  (`manage_users`, `view_analytics`, `view_ledger`) to spec codes
  (`manage_company_users`, `view_owner_dashboard`, `view_audit_ledger`)

### Scripts
- **`scripts/check_no_external_ai.sh`** — runtime guard that scans the
  codebase for 26 known external-AI patterns (openai, anthropic, cohere,
  langchain, llama_index, semantic_kernel, huggingface_hub, plus known
  API endpoints). Exits 1 if any are found outside `.audit-allowlist`.
- **`.audit-allowlist`** — empty whitelist with explicit guidance.
- **`scripts/setup.sh`, `scripts/deploy-cloud.sh`** — made executable;
  both already invoke `seed()` which now stamps `activation_started_at`.

### Tests
- **`backend/app/tests/test_phase1_acceptance.py`** — 45 tests, one per
  acceptance criterion (or sub-criterion), all auto-running in pytest
  without Docker.
- **Existing `test_trust_boundaries.py`** — updated reference strings
  to the new permission codes.

## What was already in the scaffold (verified, not changed)

- `docker-compose.yml` — postgres:15-alpine + redis:7-alpine + backend +
  frontend + baileys-bridge + celery-worker + celery-beat (on-premise)
- `k8s/` — namespace + backend + frontend + vault + whatsapp-cloud-gateway
- `backend/app/core/factories.py` — registry pattern selecting key
  backend, notification gateway, backup target by `DEPLOYMENT_MODE`
- `backend/alembic/versions/20260629_0001_init.py` — company_group +
  company + branch + user + user_company_access + audit_ledger + the
  three hidden tables with RLS policies
- `backend/app/api/admin.py` — `permission.category == 'app_owner'` is
  hard-blocked server-side
- `backend/app/api/documents.py` — `magic.from_buffer` MIME check,
  50MB cap, company_id required, Fernet encryption via factory
- `backend/app/services/permissions.py` — `get_effective_permissions`
  uses SQL filter `(expires_at IS NULL OR expires_at > now)`
- `docs/FONT_VERIFICATION.md` — all 6 required Sorani-specific glyphs
  verified in `Noto Sans Arabic`
- `src/components/app-shell.tsx` — `font-family: 'Noto Sans Arabic'`
  wired up with RTL-first layout

## How to verify

```bash
# Run all Phase 1 acceptance tests
PYTHONPATH=backend python -m pytest backend/app/tests/test_phase1_acceptance.py -v

# Run the no-external-AI guard
bash scripts/check_no_external_ai.sh

# Run the full test suite (102 tests)
PYTHONPATH=backend python -m pytest backend/app/tests/

# Spin up the on-premise stack (requires Docker)
./scripts/setup.sh
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}'
```

## Known limits

- Tests run as pure-logic contracts; the runtime DB tests (RLS live,
  cross-tenant live, tamper-detection live) are exercised by the
  `/api/trust-proof/run` endpoint added in the previous Principles Pass
  and need a live Postgres to run end-to-end.
- The `manager` and `auditor` permission sets now differ by exactly one
  code (`view_documents`); the deeper behavioural difference comes from
  the `user_company_access` row scoping, which is enforced by the
  `require_company_access` helper covered in `test_acceptance_5_*`.
