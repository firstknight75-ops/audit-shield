# AuditCore — Architecture Guide

> **Version:** 1.0.0 · **Status:** Enterprise Production-Ready (Level 5)

## Executive Summary

AuditCore is a sovereign audit intelligence platform for the Iraqi and regional
business environment. It enforces three absolute trust boundaries through
architecture (not UI hiding):

1. **Zero-Knowledge Audit** — Auditor role has zero architectural path to
   analytical outputs (`analytics_outputs`, `waste_map_items`, `risk_alerts`).
   Enforced via PostgreSQL Row-Level Security, not application-layer
   permission checks.
2. **Cross-Tenant Boundary (cloud)** — Each tenant has its own database
   schema (Essential/Advanced) or dedicated database (Elite). RLS
   `tenant_isolation_*` policies enforce isolation at the DB layer.
3. **Cross-Company-within-Tenant** — Even within a single tenant, the
   Owner's companies are isolated. `get_accessible_company_ids` enforces
   default-deny access based on `user_company_access` rows.

Plus a non-negotiable: **no OCR result is ever auto-committed without human
certification**, and **nothing in `audit_ledger` is ever updated or deleted** —
corrections are reverse entries, permanently visible next to the original.

## System Architecture

```
                          ┌──────────────────────────────┐
                          │  React 18 + Vite + Tailwind     │
                          │  (RTL-first, dark/light, WCAG) │
                          └───────────────┬───────────────┘
                                          │  HTTPS / JWT
                                          ▼
            ┌─────────────────────────────────────────────────────┐
            │  FastAPI (Python 3.11)                              │
            │  ┌──────────┬───────────┬─────────────┬──────────┐  │
            │  │  Auth   │  Trust    │  AI Engine   │ Workflow │  │
            │  │  + MFA  │  Proof    │  (local only)│ Engine   │  │
            │  └──────────┴───────────┴─────────────┴──────────┘  │
            │  ┌────────────────────────────────────────────────┐  │
            │  │  Service Layer (notifications, OCR, ledger)    │  │
            │  └────────────────────────────────────────────────┘  │
            └────────────────┬──────────────────┬───────────────┘
                             │                  │
                  ┌──────────┘                  └────────────┐
                  ▼                                            ▼
       ┌──────────────────┐                    ┌─────────────────────┐
       │  PostgreSQL 15    │                    │  Redis 7              │
       │  + RLS            │                    │  (cache, queue,       │
       │  + tsvector       │                    │   rate-limit,         │
       │  + pg_trgm        │                    │   idempotency)        │
       └──────────────────┘                    └─────────────────────┘
                  ▲
                  │
       ┌──────────┴───────────┐                ┌─────────────────────┐
       │  Celery Worker      │                │  Celery Beat          │
       │  (OCR processing,  │                │  (02:00 daily AI,    │
       │   AI orchestrator) │                │   08:00 daily tasks, │
       └────────────────────┘                │   15-min SLA sweep)   │
                                            └─────────────────────┘
                  ▲                                            ▲
                  │                                            │
       ┌──────────┴────────────────────────────────────────────┴─────┐
       │  Notification Gateway (factory)                              │
       │  On-premise → Baileys / QR auth / Redis-queued offline retry   │
       │  Cloud      → WhatsApp Cloud API / email / Slack / Teams       │
       └───────────────────────────────────────────────────────────────┘
```

## Layered Architecture

AuditCore follows **Clean Architecture** with strict layer boundaries:

```
┌─────────────────────────────────────────────────────────────────┐
│  Routes / API     →  endpoints, OpenAPI, rate limiting            │
├─────────────────────────────────────────────────────────────────┤
│  Services         →  business logic, orchestration                │
├─────────────────────────────────────────────────────────────────┤
│  Repositories     →  data access, query construction              │
│  (uses app.db.session.SessionLocal)                              │
├─────────────────────────────────────────────────────────────────┤
│  Domain Models    →  entities, enums, value objects               │
│  (SQLAlchemy 2.0 / asyncpg)                                      │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure   →  encryption, OCR, AI, notifications, cache     │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Topologies

### On-Premise (Smart Box)
```
┌─────────────────────────────────────────────┐
│  One physical Smart Box per company_group     │
│  ┌─────────┬─────────┬─────────┬──────────┐  │
│  │ Postgres│  Redis  │ Backend │ Frontend │  │
│  │   15    │    7    │ FastAPI │  Vite    │  │
│  └─────────┴─────────┴─────────┴──────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │  Baileys Bridge (WhatsApp, QR auth)   │  │
│  └───────────────────────────────────────┘  │
│  File encryption keys derived from            │
│  COMPANY_MASTER_KEY + file UUID              │
│  (raw key never stored in DB)                │
└─────────────────────────────────────────────┘
```

### Cloud
```
                ┌──────────────────────────┐
                │  Multi-tenant control plane │
                │  (App Owner Admin Panel)   │
                └──────────────────────────┘
                  ▲                  ▲
                  │ provisioning     │ ops alerts
                  │                  │
   ┌──────────────┴──┐          ┌───┴────────────────┐
   │  Tenant A       │          │  Tenant B (Elite)   │
   │  Schema: t_a    │          │  Dedicated DB       │
   │  Pooled         │          │  (VPC isolation)    │
   └─────────────────┘          └─────────────────────┘
                  ▲                          ▲
                  │                          │
            ┌─────┴──────────────────────────┴─────┐
            │  Managed Postgres + Redis + Vault     │
            │  WhatsApp Cloud API gateway             │
            └────────────────────────────────────────┘
```

## Security Model

### Defense in Depth

| Layer | Mechanism |
|---|---|
| Transport | TLS 1.2+, HSTS |
| Headers | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy |
| Rate limit | 120 rpm per IP for unauthenticated (Redis-backed token bucket) |
| Auth | JWT access (15 min) + refresh (24h), refresh-token rotation, lockout after 5 failed logins for 15 min |
| Authn (future) | MFA TOTP, SAML, OIDC, LDAP, Azure AD, Google Workspace, SCIM |
| Authz | RBAC (6 roles × 17 permissions) + ABAC (per-company overrides via `user_permission_override`) |
| DB | Row-Level Security (3 hidden tables × 2 policies each = 6 RLS predicates) |
| Tenant isolation | Schema-per-tenant (Essential/Advanced) OR dedicated-DB-per-tenant (Elite) |
| Secrets | Vault (cloud) / company-key derivation (on-prem). Keys never stored in DB |
| Audit | SHA-256 hash-chained ledger, immutable, reverse-entry only |
| Export integrity | HMAC-SHA256 tamper-proof certificate per export, public /verify endpoint |

### Trust boundaries enforced at DB level (not UI)

```sql
-- Migration 0001 enforces these for ALL three hidden tables:
ALTER TABLE analytics_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE waste_map_items  ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_alerts       ENABLE ROW LEVEL SECURITY;

CREATE POLICY auditor_no_access_analytics_outputs ON analytics_outputs
  FOR ALL USING (current_setting('app.current_user_role', true) != 'auditor');

CREATE POLICY tenant_isolation_analytics_outputs ON analytics_outputs
  FOR ALL USING (
    company_id IN (
      SELECT c.id FROM company c
      JOIN company_group cg ON cg.id = c.company_group_id
      WHERE cg.id::text = current_setting('app.current_tenant_id', true)
    )
  );
```

The application **cannot** accidentally reveal these tables to an Auditor
even via a bug — the DB itself rejects the query.

## Data Model (Corrected Ownership Hierarchy)

```
company_group  (the real tenant boundary)
  ├── id (UUID), name, tier (essential|advanced|elite)
  ├── deployment_mode (onpremise|cloud)
  ├── tenant_schema (nullable; cloud-pooled tiers only)
  ├── activation_started_at (48h SLA anchor)
  └── created_at

company  (a legal business unit; one group has 1..N)
  ├── id, company_group_id (FK), name, sector
  └── created_at

branch  (a location; one company has 1..N)
  ├── id, company_id (FK), name, location
  └── created_at

user  (a person; belongs to one group)
  ├── id, email, hashed_password, full_name, role (owner|gm|manager|auditor|admin|appowner)
  ├── company_group_id (FK), preferred_language (ar|ckb)
  ├── is_active, failed_login_attempts, locked_until, last_activity_at
  └── created_at

user_company_access  (default-deny explicit grants)
  └── user_id, company_id, branch_id (nullable=all branches), granted_by, created_at

permission  (catalog)
  └── code (unique), name, category

role_permission  (role defaults)
  └── role, permission_id

user_permission_override  (SF5.4 — temporary grant/revoke, scoped to company)
  └── user_id, permission_id, company_id (nullable=group-wide), action, reason, expires_at, is_active

audit_ledger  (immutable)
  └── company_id, actor_user_id, action_type, action_payload, created_at
      → Hash-chained: SHA-256(previous_hash + canonical_json(body))

analytics_outputs / waste_map_items / risk_alerts  (HIDDEN FROM AUDITORS)
  → RLS: current_user_role != 'auditor' AND tenant_id matches
```

## The 7 Owner Outputs

Every cycle, the Owner receives exactly 7 deliverables:

| # | Output (AR)            | Output (EN)             | First-class deliverable? |
|---|------------------------|------------------------|--------------------------|
| 1 | الصورة الحقيقية       | The True Picture       | Yes |
| 2 | مؤشر الموثوقية        | Trust Index            | **Yes** — standalone page, breakdown + 6-cycle trend |
| 3 | خريطة الهدر           | Waste Map              | Yes |
| 4 | خريطة المخاطر         | Risk Map               | Yes |
| 5 | خريطة الفرص           | Opportunity Map        | Yes (NEW in Phase 3) |
| 6 | خطة العمل             | Action Plan            | Yes (Change + Adaptation paths) |
| 7 | لوحات القيادة         | Role Dashboards        | Yes |

Plus: Activation tracker, Portfolio (multi-company), Trust Center (proof).

## Operational Guarantees

| SLA | Target | How |
|---|---|---|
| First login after install | ≤ 30 min (on-prem), ≤ 10 min (cloud) | `install.sh` / `deploy-cloud.sh` |
| First real report after install | ≤ 48 h | 4-stage activation tracker |
| OCR throughput | 3 s/page | Tesseract with `lang='ara'` + pdf2image |
| Daily analysis | < 1 h for ~10,000 tx/day | Celery-Beat at 02:00 Baghdad |
| API p50 | < 150 ms | Prometheus metrics + indexed queries |
| Concurrent users | 1000+ | Async FastAPI + Redis cache + connection pooling |
| Audit chain integrity | 100% | SHA-256 chain + nightly verify job |

## Why we cannot "accidentally" violate the principles

| Failure mode | Why it's prevented |
|---|---|
| Auditor reads analytics | RLS `auditor_no_access_*` policy — DB-level |
| Manager sees other company's data | `user_company_access` rows are default-deny; `require_company_access` returns False if no row |
| App Owner reads tenant financial data | App Owner has only `app_owner_*` permissions; queries use only `inventory.*` schema tables |
| Ledger tampered with directly | Hash chain detects; verification endpoint flags exact broken entry |
| External AI API call added | CI guard `scripts/check_no_external_ai.sh` fails the build |
| Chatbot added | Same guard — `/chat`, `/assistant`, `/llm` paths rejected |
| OCR auto-commits | Workflow: `pending → certified`; low-confidence fields block certify |
| Tenant data leaks cross-tenant | RLS `tenant_isolation_*` + factory-based key derivation |

## See also

- [PRINCIPLES_PASS.md](PRINCIPLES_PASS.md)
- [PHASE1_FOUNDATION.md](PHASE1_FOUNDATION.md) — Trust boundaries
- [PHASE2_TRUST_LAYER.md](PHASE2_TRUST_LAYER.md) — Auditor + reverse entries
- [PHASE3_AI_AND_DASHBOARD.md](PHASE3_AI_AND_DASHBOARD.md) — AI + Trust Center
- [PHASE4_SELLABLE.md](PHASE4_SELLABLE.md) — Verification + App Owner
- [DEPLOYMENT.md](DEPLOYMENT.md) — Both modes
- [SECURITY.md](SECURITY.md) — Security model
- [docs/adr/](docs/adr/) — Architecture Decision Records
- [RUNBOOK.md](RUNBOOK.md) — Operator runbook
- [API_GUIDE.md](API_GUIDE.md) — API reference
