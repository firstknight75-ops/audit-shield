# Foundation Deep Pass — Status Report

**Commit:** `3002c57`  
**Branch:** `main`  
**Date:** 2026-06-29

## Completed in This Pass

### 1. Alembic Migration (Critical Blocker — Fixed)
- **Old:** `20260628_0001_init.py` — had old schema with `company.tier`, `user.company_id`, `user.branch_id`, no `company_group`, no `user_company_access`, no `preferred_language`, no `translation`
- **New:** `20260629_0001_init.py` — full new schema:
  - `company_group` table (tenant boundary)
  - `company` with `company_group_id` FK
  - `branch` under `company`
  - `user_account` with `company_group_id` FK + `preferred_language`
  - `user_company_access` table
  - `analytics_outputs`, `waste_map_items`, `risk_alerts` all have `branch_id`
  - `user_permission_override` has optional `company_id`
  - `translation` table with unique `(key, language)`
  - RLS policies: auditor denial + tenant isolation on hidden tables
  - `set_user_role()` + `app.current_tenant_id` session variable

### 2. All API Routes Refactored (30 access-control points)
- **admin.py:** User creation uses `company_group_id`, `CompanyAccessGrant[]`, `require_company_access()`. Activity feed filters by accessible companies. Branch listing requires company access. Added `GET /admin/companies` and `POST /admin/language`.
- **analytics.py:** All endpoints take `company_id` as `Query(...)`. Every query uses `require_company_access()`. Manager dashboard takes optional `branch_id`.
- **certification.py:** Uses `get_accessible_company_ids()` for document scoping. Certification checks access to company.
- **owner.py:** Ledger verify/tamper/auditor-efficiency all take `company_id` query param. Auditor efficiency queries via `UserCompanyAccess`.
- **phase4.py:** Manager widgets, exports, what-if all take `company_id`. App owner routes use translated strings.
- **documents.py:** Already updated in prior commit — requires `company_id` + `branch_id` on upload.

### 3. Access Control Service Enhanced
- `get_accessible_company_ids(user, session)` — returns company IDs from `user_company_access`
- `get_accessible_companies(user, session)` — returns structured `[{company_id, name, branches}]` for `/auth/me`
- `require_company_access(user, session, company_id, branch_id?)` — default-deny, role-aware
- `get_accessible_branch_ids(user, session, company_id)` — branch-level scoping

### 4. i18n Fully Expanded (30+ keys, ar + ckb)
- **Backend:** `TRANSLATIONS` dict covers: auth (6), permissions (1), documents (5), admin (6), analytics (4), certification (3), owner (2), manager (1), exports (1), whatif (1), appowner (8), ledger (2) = 40 keys × 2 languages = 80 translation pairs
- **All API error/response messages** now use `tr(key, lang)` instead of hardcoded Arabic
- **Ledger messages** now use i18n (chain broken, intact)

### 5. Language Persistence Endpoint
- `POST /admin/language` — accepts `{preferred_language: "ar"|"ckb"}`, validates, persists to `user.preferred_language` in DB
- Frontend `persistLanguageChange()` calls this on toggle

### 6. Auth Schema Typed
- `MeResponse` now has `accessible_companies: list[AccessibleCompany]` with `AccessibleBranch`
- Clean Pydantic models instead of `list[dict]`

### 7. Session Context for RLS
- `set_session_context()` now sets both `app.current_user_role` AND `app.current_tenant_id`
- Tenant ID = `user.company_group_id` — used by RLS tenant isolation policy

### 8. Workers Updated
- `generate_daily_tasks` now verifies `UserCompanyAccess` for auditor→company mapping
- Branch-scoped auditor access is respected
- No more `auditor.company_id` reference

### 9. Seed Data
- Seeds ALL translations from `TRANSLATIONS` dict to `Translation` table
- Every seeded user has `preferred_language` set
- `UserCompanyAccess` rows for correct scoping:
  - Owner/GM: both companies, all branches
  - Manager: company A only, all branches
  - Auditor: company A, branch 1 only
  - Admin: both companies

### 10. Frontend i18n Expanded
- 4 namespaces: `auth`, `dashboard`, `certification`, `admin`
- Full `ar.json` + `ckb.json` for each
- App-shell uses namespace-based `t(ns, key, locale)` for all nav labels
- Language switcher label: **لغة / زمان**
- Font: `'Noto Sans Arabic', 'Noto Sans Arabic UI', sans-serif`

### 11. Sorani Font Verification Documented
- `docs/FONT_VERIFICATION.md` with:
  - All 6 required Sorani glyphs with Unicode points
  - Test sentence using all letters
  - Verification procedure
  - Font source link

### 12. Main.py Lifespan
- Auto-seeds on startup if `CompanyGroup` doesn't exist
- Phase4 router included

---

## Remaining Gaps (Next Pass)

### High Priority
1. **Frontend pages beyond login/app-shell** — most route pages (owner, manager, auditor, admin) still have hardcoded Arabic strings and don't pass `company_id` query params
2. **Full i18next migration** — current frontend uses a lightweight custom helper, not full `i18next` with lazy loading
3. **Admin multi-company UI** — company picker, user creation form with `company_access` multi-select, branch picker
4. **Acceptance tests for new scoping** — manager company A vs B, auditor branch 1 vs 2, `/auth/me` differences

### Medium Priority
5. **DB-backed translation lookup** — `tr()` currently uses in-memory dict; should fall through to `Translation` table at runtime
6. **Analytics routes** should check `auditor` role explicitly to deny `analytics_outputs`, `waste_map_items`, `risk_alerts` (defense in depth beyond RLS)
7. **Frontend route pages** need `company_id` state management (which company the user is viewing)

### Low Priority
8. **CSS logical properties audit** — ensure no hardcoded `left`/`right` in custom CSS
9. **WhatIfRequest schema** still has `implementation_months` that doesn't match the Pydantic model
10. **Existing test files** need review for any assumptions about old schema
