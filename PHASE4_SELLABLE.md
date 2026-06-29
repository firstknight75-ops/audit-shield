# AuditCore — Phase 4: Sellable Product

**Branch:** `auditcore/phase4-sellable`
**Date:** 2026-06-29

This phase makes AuditCore sellable: real exportable verifiable outputs,
the App Owner's command center, the cross-client template/CRaaS pipeline,
and operational proof of the 48-hour activation promise — across both
on-premise Smart Boxes and cloud tenants.

## Acceptance criteria — all auto-tested

| # | Criterion | Tests |
|---|---|---|
| 1 | PDF renders every Kurdish-Sorani-specific letter correctly | 3 |
| 2 | `/verify/{report_id}` confirms untampered + flags tampered; no login; no content exposure | 7 |
| 3 | What-If never merges two companies' figures | 4 |
| 4 | App Owner Clients tab: zero financial-schema joins; pooled→elite migration no-data-loss | 5 |
| 5 | 48-hour activation: stage-4 ≤ 48h → completion banner; overdue → App Owner flag | 7 |
| 6 | Backup/restore atomic per company_group | 3 |
| 7 | App Owner zero visibility preserved through all Phase 4 work | 4 |
| Ops | DEPLOYMENT.md, SECURITY.md, install.sh, deploy-cloud.sh | 5 |

**Result:** `38 passed` on `test_phase4_acceptance.py`, **221 passed, 1 skipped** total.

## What Phase 4 added

### 1. Export engine — Excel/PDF/PNG with tamper-proof certificates
- `backend/app/exports/engine.py` — all three formats now accept a `cert` dict
  and emit `report_id`, `ledger_hash_at_generation`, `signature`, and
  `verify_url` on every output.
- **PDF uses Noto Sans Arabic** (verified Phase 1 Sorani coverage) as the
  primary font, with `Noto Naskh Arabic`, `Cairo`, `Amiri`, `DejaVu Sans`
  as system fallbacks. Render direction `rtl` + `unicode-bidi: embed`.
- **Pillow PNG** picks the best available TTF (Noto Sans Arabic preferred),
  not the default bitmap font that drops Sorani glyphs.
- Every export carries a `report_id` UUID + `verify_url` that links to
  the public `/verify/{report_id}` endpoint.

### 2. Public report verification `/verify/{report_id}` — NO LOGIN
- `backend/app/api/verify.py` — POST endpoint, **no `get_current_user` dependency**.
- Re-derives the HMAC-SHA256 signature from server-stored metadata and
  returns ONLY:
  - `valid: bool`
  - bilingual verdict message
  - structured `checks` block
  - `note: "No content disclosed — integrity verdict only."`
- Returns the same response shape for "wrong report_id" vs "tampered" to
  prevent enumeration attacks.

### 3. What-If Decision Simulator
- Single-company scope enforced: `company_id: str = Query(...)` is the
  only input — no `company_ids: list` parameter exists anywhere.
- WasteMapItem lookup is explicitly scoped: `WasteMapItem.company_id == company_id`.
- Both `/what-if/run` and `/what-if/export` endpoints preserved with this invariant.

### 4. No-Code Template Engine & CRaaS (already scaffolded, verified)
- `backend/app/templates/builder.py` — `SECTOR_PRESETS` for Manufacturing,
  Restaurants, Real Estate, Trading; each preset is a list of widget codes.
- Templates stored as JSON with `name`, `sector`, `widgets` — **language
  is a render-time dimension**, never baked into the JSON.
- `POST /appowner/templates/{id}/push` records `transport=vpn` or `cicd`
  in the immutable `inventory_appowner_audit` log.
- `POST /appowner/craas` queues custom-report requests.

### 5. App Owner Admin Panel — clients + tier + templates + maintenance
- **Clients tab:** every `company_group` (real tenant/Smart Box/cloud account).
  Tier, user_count vs. user_cap, deployment_mode, last health-check,
  last backup. **Zero financial-schema joins** — all queries are on
  `inventory.*` tables only.
- **License & tier management:** `POST /appowner/clients/{id}/tier` —
  upgrading a cloud pooled tenant to Elite provisions a dedicated DB
  URL and clears `tenant_schema`, with the change recorded in
  `inventory_appowner_audit`.
- **Permission templates:** `POST /appowner/templates`, `push`, `rollback` —
  edits never retroactively touch a running client without explicit push.
- **Maintenance & Audit tab:** every App-Owner action is logged with
  timestamp + target client; the same log surfaces to each client in
  their Trust Center (Phase 3) as proof of visibility.

### 6. 48-Hour Activation Tracker (4 stages)
- `backend/app/services/activation_tracker.py` — `compute_activation_progress()`,
  `flag_overdue_installs()`.
- 4 stages: تثبيت الجهاز → تهيئة المستخدمين → أول دفعة مستندات → أول تحليل وتقرير
- Stages auto-bootstrap from observable data (no manual bookkeeping).
- **Shareable completion banner:** "تم تفعيل أول تقرير حقيقي خلال [X] ساعة"
- **Overdue flag:** any install exceeding 48h without stage 4 appears in
  `GET /appowner/overdue-installs`.

### 7. Deployment & operations, both modes
- `install.sh` — on-prem under 30 min to first login
- `backup.sh` — atomic per company_group (all companies + branches)
- `healthcheck.sh` — disk/RAM/UPS, alert on failure
- `update.sh` — VPN pull, backup-first, rollback on failed health check
- `deploy-cloud.sh` — provisions schema or dedicated DB per tier, sets
  Vault secrets, registers with App Owner inventory
- `migrate-tenant-to-elite.sh` — pooled → dedicated DB with no data loss
- `DEPLOYMENT.md` + `SECURITY.md` — both modes documented side-by-side

## Migration added

`backend/alembic/versions/20260629_0003_report_certificates_activation.py`:
- `report_certificate` table — stores every exported report's certificate
- `activation_milestone` table — records the 4 activation stages per group

## Files added (Phase 4 only)

### Backend
- `backend/app/api/verify.py` — public verification endpoint
- `backend/app/api/activation.py` — activation progress + overdue endpoints
- `backend/app/services/activation_tracker.py` — 48h tracking logic
- `backend/app/exports/certificates.py` — rewritten with `report_id` + payload support
- `backend/app/exports/engine.py` — updated for cert + Sorani-capable fonts
- `backend/app/models/entities.py` — added `ReportCertificate`, `ActivationMilestone`
- `backend/alembic/versions/20260629_0003_report_certificates_activation.py` — migration

### Backend tests
- `backend/app/tests/test_phase4_acceptance.py` — 38 tests

### Frontend
- The Phase 4 export/verify/activation UIs already exist (mock-data-driven);
  the backend contracts are now solid and ready for live wiring.

## Cumulative across all 4 phases + Principles Pass
- **Acceptance tests:** 45 (Phase 1) + 38 (Phase 2) + 43 (Phase 3) + 38 (Phase 4) + 39 (trust boundaries) + 10 (owner outputs) = **213 acceptance + boundary tests**
- Plus regression tests = **221 passing total, 1 skipped**
- No-external-AI guard: **PASS**

## How to verify end-to-end

```bash
./scripts/setup.sh
# Login as owner
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}' | jq -r .access_token)

# Generate an export (gets report_id back)
curl -X POST http://localhost:8000/api/exports/run?company_id=<id> \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"output_code":"waste_map","format":"pdf"}'
# → { report_id, certificate, verify_url }

# Anyone can verify it (no login)
curl -X POST http://localhost:8000/verify/<report_id> \
  -H 'Content-Type: application/json' \
  -d '{"ledger_hash_at_generation":"...","signature":"...","payload":{...}}'

# Check activation progress (Owner)
curl http://localhost:8000/api/owner/activation-progress?company_id=<id> \
  -H "Authorization: Bearer $TOKEN"

# Check overdue installs (App Owner)
curl http://localhost:8000/api/appowner/overdue-installs \
  -H "Authorization: Bearer <appowner-token>"
```
