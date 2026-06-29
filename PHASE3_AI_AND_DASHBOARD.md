# AuditCore — Phase 3: AI Engine + Dashboard Design System

**Branch:** `auditcore/phase3-ai-and-design`
**Date:** 2026-06-29

Phase 3 builds the AI engine and a dashboard that is genuinely professional
— proving, not asserting, the trust guarantees this product is built on.

## Acceptance criteria — all auto-tested

| # | Criterion | Tests |
|---|---|---|
| 1 | 10+ certified invoices + manual trigger → waste_map_items with IQD figures; duplicate + procurement/inventory mismatch flagged | 4 |
| 2 | Each company's Trust Index + daily run is independent | 3 |
| 3 | Portfolio conditional render + persistent switcher | 5 |
| 4 | `/trust` shows live real data for every claim in both languages | 6 |
| 5 | `/owner/trust-index` shows breakdown + 6-cycle trend | 4 |
| 6 | Full visual polish in ckb equal to ar | 6 |
| 7 | Auditor 403 on every owner-dashboard endpoint | 3 |
| 8 | Manager sees only accessible companies/branches/departments | 3 |
| 9 | Critical alerts deliver in recipient's preferred language via correct gateway | 5 |
| Bonus | Bilingual narrative (ar + ckb, audience-aware) | 3 |

**Result:** `43 passed` on `test_phase3_acceptance.py`, **183 passed, 1 skipped** total.

## AI Engine — all local, deterministic, no external APIs

| Module | Purpose |
|---|---|
| `data_quality.py` | Duplicates, mismatches, missing fields, out-of-sequence docs |
| `anomaly.py` | Z-score >3, IQR outliers, serial gaps; activates only at ≥30 docs (avoids false positives on thin baselines) |
| `cross_reference.py` | AI Bridge — procurement vs bank outflow (1%), procurement vs inventory received (5%); variance_amount in IQD |
| `impact.py` | Findings → explicit IQD figures → `waste_map_items` |
| `predictor.py` | Lightweight sklearn regression for next-month cash outflow + stockout risk |
| `narrative.py` | Bilingual (ar + ckb), audience-aware (Owner = strategic, Manager = operational), deterministic hash for cache |
| `orchestrator.py` | Celery task `run_daily_analysis(company_id)` — **per company, never per group**; 02:00 Baghdad |

## Dashboard Design System

Tokens decided in `src/styles.css`:
- **Sacred status colors:** `--success` (Green, healthy), `--warning` (Yellow, mid), `--danger` (Red, critical) — used ONLY for status
- **Single accent:** warm gold `--primary: oklch(0.78 0.13 82)` — calm, confident, NOT generic SaaS blue
- **Restrained neutrals:** deep ink `--background` + warm `--foreground`
- **Typefaces:** Tajawal (display, headlines + Executive-layer numbers) + Cairo (body, both verified for Arabic + Kurdish Sorani in Phase 1)
- **8px baseline, one radius (`--radius: 0.625rem`), one shadow used consistently**

Signature element: **Trust Index radial arc** — used nowhere else as a generic progress bar.

## Screens — built

### Portfolio view `/owner/portfolio`
- Card per company with name, waste (IQD), Trust Index, alerts, branch count
- **Side-by-side display explicitly labeled:** "عرض جنباً إلى جنب — بدون دمج الأرقام" / "پیشاندانی لاتەنیشت — بەبێ تێکەڵکردنی ژمارەکان" — the UI itself enforces the no-blend rule
- Totals block labeled explicitly as SUM, not blended

### Executive layer `/owner`
- **Exactly 5 cards** (per NF5.3): إجمالي الهدر الشهري، مؤشر الثقة، عدد التنبيهات الحرجة، الكاش المتوقع، كفاءة فريق التدقيق
- Big numbers use `font-display` (Tajawal) for hierarchy
- All copy bilingual

### Trust Center `/trust` (signature page)
- **Live data from `/api/trust-proof/run`** — proves RLS, ledger integrity, tenant isolation, app-owner zero-visibility
- **Live `/health`** call shows real `DEPLOYMENT_MODE` with bilingual explanation of what it means in practice
- **Live denied-attempt counter** computed from the auditor probe result
- **Linked to Phase 1 CI guard** (`scripts/check_no_external_ai.sh`)
- Public/no-login version with deterministic fallback so the proof structure is always visible

### Persistent company/branch switcher
- Lives in the top bar at every layer
- **Auto-skips** when the user has exactly one company with ≤1 branch (single-company Owner)
- Persists selection to `localStorage` (auditcore.active.company / branch)
- Lets the Owner move sideways without retracing to Portfolio

### Other screens already built (Phase 1/2 work, verified)
- Trust Index standalone `/owner/trust-index` — score breakdown + 6-cycle trend
- Departments layer (toggleable)
- Manager dashboard
- Layer 4 raw document viewer
- Ledger viewer with reverse-entry support

## Notifications & WhatsApp

- `NotificationGateway` interface — Baileys (onprem) or WhatsAppCloud (cloud), same call signature
- Factory picks the right gateway based on `DEPLOYMENT_MODE`
- Severity routing:
  - Critical → immediate push (bypasses DND)
  - High → queued, 07:00 daily digest
  - Low → in-app only
- Templates in both ar + ckb, delivered in recipient's `preferred_language`
- **DND default 23:00–06:00** (`in_dnd_window(start=23, end=6)`)
- 5-minute Redis-queued offline retry (Phase 4)

## How to verify

```bash
# All Phase 3 tests
PYTHONPATH=backend python -m pytest backend/app/tests/test_phase3_acceptance.py -v

# Full suite
PYTHONPATH=backend python -m pytest backend/app/tests/

# CI guard
bash scripts/check_no_external_ai.sh

# Live runtime
./scripts/setup.sh
# 1. Login as owner
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}' | jq -r .access_token)

# 2. Trigger daily analysis (manual)
curl -X POST http://localhost:8000/api/analytics/run/<company_id> \
  -H "Authorization: Bearer $TOKEN"

# 3. Visit /trust — proves guarantees with live data
curl http://localhost:8000/api/trust-proof/run -H "Authorization: Bearer $TOKEN"
```
