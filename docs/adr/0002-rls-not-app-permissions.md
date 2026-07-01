# ADR-0002: Enforce Auditor Boundary in PostgreSQL RLS, Not Application Layer

## Status

Accepted · 2026-06-29 · Supersedes any "check role in Python" approach.

## Context

The Auditor must NEVER see `analytics_outputs`, `waste_map_items`, or
`risk_alerts`. Two architectural options were on the table:

1. **Application-layer enforcement** — every API endpoint checks
   `current_user.role != 'auditor'` before returning analytics.
2. **Database-layer enforcement via Row-Level Security** — Postgres RLS
   policies filter rows by session variable `app.current_user_role`.

## Decision

We chose **(2) RLS at the database layer** as the canonical enforcement
mechanism. Application-layer checks are kept as **defense in depth** but
are NOT the boundary.

## Rationale

- A future API endpoint that forgets the `role != 'auditor'` check would
  leak data — but with RLS, even a buggy endpoint cannot leak.
- The boundary survives future code paths (raw SQL queries, ad-hoc
  dashboards, BI tools, third-party integrations).
- The `app.current_user_role` session variable is set in a single place
  (`set_session_context` in `app/db/session.py`) called from `get_current_user`.
- Migration `20260629_0001_init.py` creates the policies:
  - `auditor_no_access_<table>` → `current_setting('app.current_user_role', true) != 'auditor'`
  - `tenant_isolation_<table>` → `JOIN company_group ... cg.id::text = current_setting('app.current_tenant_id', true)`

## Consequences

- **+** The trust boundary cannot be accidentally violated by application bugs.
- **+** Migration `0001` is the single source of truth — readable, reviewable.
- **+** `Phase 1 acceptance #3` proves it via the migration content test.
- **−** Requires every backend connection to set `app.current_user_role`
  via `set_session_context` BEFORE running queries (handled in `get_current_user`).
- **−** Tests that bypass session-context need to set it explicitly.

## Verification

- `backend/app/tests/test_phase1_acceptance.py::TestAuditorRLSContract`
- `backend/app/tests/test_rls_and_manager_scope.py::TestAuditorRLSContract`
- Live runtime tests gated by `AUDITCORE_TEST_DATABASE_URL` env var
