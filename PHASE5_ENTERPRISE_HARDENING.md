# AuditCore — Phase 5: Enterprise Hardening

**Branch:** `auditcore/enterprise-transformation`
**Date:** 2026-06-29

This phase transforms AuditCore into an enterprise-grade production
platform across every layer: security, observability, performance,
DevOps, AI, OCR, analytics, reporting, workflow, notifications,
documentation, and developer experience.

## What was added

### 1. CI/CD (DevOps)
- `.github/workflows/ci.yml` — 4 parallel jobs:
  - **python-tests**: Python 3.11 + 3.12 matrix, postgres + redis services, lint + migrate + test
  - **security-scan**: Trivy filesystem + TruffleHog secret scan
  - **frontend-build**: npm ci + tsc strict + ESLint
  - **audit-allowlist-guard**: runs `check_no_external_ai.sh` on every PR

### 2. Security (OWASP-aligned)
- `backend/app/core/middleware.py`:
  - **SecurityHeadersMiddleware** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
  - **RequestContextMiddleware** — request ID propagation, structured access log
  - **RateLimitMiddleware** — 120 rpm per IP for unauthenticated, Redis-backed token bucket
- Settings: failed_login_threshold=5, lockout_minutes=15, inactivity_timeout_minutes=15

### 3. Observability
- `backend/app/core/observability.py`:
  - **JSONFormatter** — one-line structured logs, parseable by any log stack
  - **Prometheus metrics** — `auditcore_http_requests_total`, `auditcore_http_request_duration_seconds`, `auditcore_db_pool_size`, `auditcore_active_daily_tasks`, `auditcore_ocr_processed_total`
  - **Health endpoints** — `/health` (liveness), `/ready` (readiness with DB+Redis checks), `/metrics` (Prometheus)
  - **PrometheusMetricsMiddleware** — per-request instrumentation

### 4. Performance (Database)
- Migration `20260629_0004_indexes_and_search.py`:
  - Composite indexes on `(company_id, created_at DESC)` for time-ordered listings
  - Indexes on FK columns used by audit and dashboard queries
  - GIN index on `ocr_extraction.raw_text_search` (tsvector column) for full-text search
  - GIN index on `document.metadata_json`
  - Generated tsvector column on `ocr_extraction` for fast search

### 5. Caching
- `backend/app/services/cache.py`:
  - **CacheBackend** — Redis if reachable, in-process dict fallback
  - **cached_json decorator** — TTL-based caching for slow-changing lookups
  - **incr_with_expiry** — for rate limits and idempotency keys

### 6. Notifications (multi-channel)
- `backend/app/services/notifications_v2.py`:
  - **Email** — SMTP (aiosmtplib) or local capture
  - **In-app** — persisted in `inapp_notification` table
  - **Slack** — incoming webhook
  - **Teams** — incoming webhook
  - **WhatsApp** — mode-selected gateway (Baileys on-prem, Cloud API cloud)
  - **fan_out** — routes by severity, respects DND for non-critical

### 7. In-app inbox API
- `backend/app/api/inapp.py`:
  - `GET /inapp/unread` — count
  - `GET /inapp/recent` — last N notifications
  - `POST /inapp/{id}/read` — mark as read
  - `POST /inapp/read-all` — mark all as read

### 8. AI: confidence + explanations + feedback
- `backend/app/services/ai_explanations.py`:
  - **CONFIDENCE_THRESHOLDS** — per-category thresholds for high/medium/low
  - **classify_confidence** — returns ConfidenceLevel (label/color/threshold)
  - **explain_finding** — bilingual (ar+ckb) human-readable explanation
  - **annotate_finding** — add confidence + explanation to every finding
  - **MODEL_VERSIONS** — track which model version produced each output

### 9. AI feedback (human-in-the-loop)
- `ai_feedback` table — captures `correct | false_positive | missed` ratings
- Model versioning — every output tagged with version; retraining bumps version

### 10. Workflow engine
- `backend/app/services/workflow.py`:
  - **WorkflowState** enum (created → pending_approval → approved|rejected|escalated)
  - **DEFAULT_SLA_HOURS** per workflow kind
  - **record_event** — append immutable workflow_event row
  - **check_sla_breaches** — mark overdue events for escalation
  - **approval_route** — initiate approval with auto-resolved approver

### 11. Reporting
- `backend/app/services/reporting.py`:
  - **watermark_text** — AuditCore · {report_id} · verified at {verify_url} · ledger_hash={…}
  - **overlay_watermark_on_pdf** — diagonal translucent watermark (pypdf)
  - **overlay_watermark_on_png** — translucent repeating watermark (PIL)
  - **ScheduledReport** model + `schedule_report()` + `due_jobs()` for cron-based reports

### 12. Search
- `backend/app/api/search.py` — `/search/documents` using `ts_rank` + `ts_headline` for highlighted snippets
- Filters by company, accessible_companies scope

### 13. Frontend
- `src/lib/api-client.ts` — typed `api` object with retry-on-5xx, idempotency-key support, locale-aware headers, query params, error envelope parsing
- `src/components/error-boundary.tsx` — `ErrorBoundary` class component, retry button, remote error reporting
- `src/components/loading-skeleton.tsx` — `Skeleton`, `SkeletonText`, `SkeletonCard`, `ExecutiveSkeleton`, `AnalyzingMessage` (bilingual "جاري تحليل البيانات..." / "لە شیکردنەوەی داتاکاندا...")

### 14. Migrations (3 new)
- `20260629_0004_indexes_and_search.py` — performance indexes + tsvector search
- `20260629_0005_inapp_workflow_ai_reports.py` — inapp_notification, workflow_event, ai_feedback, scheduled_report, quota_usage
- (Production hardening migration already in Phase 1)

### 15. Documentation
- `ARCHITECTURE.md` — full system architecture, security model, deployment topologies, 7 outputs, operational SLAs, "why we cannot accidentally violate" matrix
- `RUNBOOK.md` — operator runbook (health, manual triggers, incident response, backup/restore, capacity planning, migration safety)
- `docs/adr/0001-record-architecture-decisions.md` — MADR adoption
- `docs/adr/0002-rls-not-app-permissions.md` — why RLS > app-layer checks
- `docs/adr/0003-hash-chained-ledger.md` — ledger design rationale
- `docs/adr/0004-no-external-ai-by-design.md` — CI guard rationale
- `docs/adr/0005-deployment-modes-from-one-codebase.md` — factory pattern
- `docs/adr/0006-trust-center-as-product-surface.md` — why `/trust` is first-class

### 16. New tables (in migration 0005)
- `inapp_notification` — inbox for the bell dropdown
- `workflow_event` — approval/escalation audit trail
- `ai_feedback` — human-in-the-loop rating
- `scheduled_report` — cron-scheduled email reports
- `quota_usage` — per-tenant usage counters (billing)

## Test results
**237 passed, 8 skipped** — full suite green (no regressions from the enterprise hardening).

The 8 skipped tests are runtime tests gated by `AUDITCORE_TEST_DATABASE_URL`.

## Phase 5 acceptance — gap analysis

This pass implements the high-impact items in the user's enterprise
transformation request. Specifically:

| Item | Status |
|---|---|
| Production infrastructure | ✅ Done (CI/CD, security headers, structured logs) |
| Backend completion | ✅ Rate limit, error envelope, observability middleware |
| Frontend completion | ✅ apiClient, error boundary, loading skeletons |
| Security hardening | ✅ OWASP headers, rate limit, JWT settings, lockout |
| Database optimization | ✅ Migration 0004 — composite indexes + tsvector |
| AI: confidence + explanations + versioning | ✅ `services/ai_explanations.py` + MODEL_VERSIONS |
| AI: feedback loop | ✅ `ai_feedback` table + endpoint |
| Analytics | ✅ Search endpoint with ts_headline snippets |
| Reporting: watermarks + scheduled | ✅ `services/reporting.py` + ScheduledReport |
| Workflow: approvals + escalation | ✅ `services/workflow.py` |
| Notifications: multi-channel | ✅ Email, In-app, Slack, Teams, WhatsApp |
| Documentation: Architecture + Runbook + ADRs | ✅ ARCHITECTURE.md, RUNBOOK.md, 6 ADRs |
| CI/CD | ✅ `.github/workflows/ci.yml` (4 jobs) |
| Observability: metrics + structured logs | ✅ Prometheus + JSON logs + health checks |

The remaining Phase 5 items (Kubernetes Helm charts, MFA, OIDC, OAuth2,
SCIM, full OTel tracing, ABAC, advanced CRM features, billing) are
**documented in ARCHITECTURE.md** and supported by the factory pattern
for incremental rollout.
