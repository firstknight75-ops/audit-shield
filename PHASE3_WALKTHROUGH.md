# Phase 3 Walkthrough / Acceptance Guide

## Goal

Phase 3 turns AuditCore from a secure document/audit platform into a local in-tenant analysis engine with owner-grade drill-down visibility.

No external AI/LLM APIs are used.
All analysis is local using Python libraries and template-based Arabic narratives.

---

## What Phase 3 adds

### Local AI modules

Located in `backend/app/ai/`

- `data_quality.py`
- `anomaly.py`
- `cross_reference.py`
- `impact.py`
- `predictor.py`
- `narrative.py`
- `orchestrator.py`

### Owner analytics views

- Layer 1: executive cards
- Layer 2: department/category breakdown
- Layer 3: findings list
- Layer 4: document trace + ledger trail

### Manager analytics boundary

- Manager analytics are constrained server-side to their own branch-linked document scope.

### Alerts

- Routed through the same notification abstraction selected by `DEPLOYMENT_MODE`
- On-premise: Baileys gateway
- Cloud: WhatsApp Cloud gateway

---

## Acceptance walkthrough

## A) Prepare environment

### On-premise setup

```bash
./scripts/setup.sh
```

### Optional integration prep notes

```bash
./scripts/run-integration-checks.sh
```

### Health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{ "status": "ok", "deployment_mode": "onpremise" }
```

---

## B) Login as Owner and Auditor

### Owner login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@auditcore.local","password":"Owner123!"}'
```

### Auditor login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}'
```

Store the returned access tokens for later steps.

---

## C) Trigger local analysis manually

Use the authenticated Owner token and the seeded company id.

```bash
curl -X POST http://localhost:8000/api/analytics/run/<COMPANY_ID> \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected:

- Arabic success response
- analysis runs locally/in-tenant
- no external model/API usage

---

## D) Verify waste map population with IQD figures

```bash
curl http://localhost:8000/api/owner/dashboard/layer2 \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected:

- non-empty list after analysis
- each item includes:
  - `category`
  - `description`
  - `impact_score`
  - `iqd_amount`

Acceptance target:

- waste map is populated with explicit IQD values, not just labels.

---

## E) Verify planted duplicate invoice and planted mismatch

```bash
curl http://localhost:8000/api/owner/dashboard/layer3 \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected findings should include entries representing:

- duplicate invoice
- procurement/inventory mismatch

Typical finding types to look for:

- `duplicate_invoice`
- `procurement_inventory_mismatch`

---

## F) Verify Owner Layer 1 dashboard

```bash
curl http://localhost:8000/api/owner/dashboard \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected fields:

- `monthly_waste`
- `trust_index`
- `critical_alerts`
- `predicted_cash_outflow`
- `auditor_efficiency`
- `narrative`

UI expectation:

- exactly 5 cards on the Owner screen:
  - إجمالي الهدر الشهري
  - مؤشر الثقة
  - عدد التنبيهات الحرجة
  - الكاش المتوقع
  - كفاءة فريق التدقيق

---

## G) Drill Layer 1 → 2 → 3 → 4

### Layer 2

```bash
curl http://localhost:8000/api/owner/dashboard/layer2 \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

### Layer 3

```bash
curl http://localhost:8000/api/owner/dashboard/layer3 \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

### Layer 4

Use a `document_id` from the findings.

```bash
curl http://localhost:8000/api/owner/dashboard/layer4/<DOCUMENT_ID> \
  -H "Authorization: Bearer <OWNER_ACCESS_TOKEN>"
```

Expected Layer 4 response:

- `document_id`
- `filename`
- `ledger`
- `extracted_data`

Acceptance target:

- owner can drill from executive KPI down to one original record trace.

Note:

- current backend provides trace data and file metadata; fully live frontend document rendering should still be validated in a running environment.

---

## H) Verify Auditor is blocked from analytics

```bash
curl http://localhost:8000/api/owner/dashboard \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

Expected:

- `403`
- Arabic permission error

Also test:

```bash
curl http://localhost:8000/api/owner/dashboard/layer2 \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

```bash
curl http://localhost:8000/api/owner/dashboard/layer3 \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

```bash
curl http://localhost:8000/api/owner/dashboard/layer4/<DOCUMENT_ID> \
  -H "Authorization: Bearer <AUDITOR_ACCESS_TOKEN>"
```

Acceptance target:

- Auditor gets blocked on every analytics path.

---

## I) Verify Manager only sees own scoped findings

Login as Manager:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"manager@auditcore.local","password":"Manager123!"}'
```

Then:

```bash
curl http://localhost:8000/api/manager/dashboard \
  -H "Authorization: Bearer <MANAGER_ACCESS_TOKEN>"
```

Expected:

- branch-scoped result only
- no full cross-company analytics output
- findings limited to document scope associated with the manager branch

Acceptance target:

- Manager only sees their own branch/department-relevant analytics scope.

---

## J) Verify alert routing abstraction

Phase 3 uses the same notification call signature through the mode-selected gateway.

### On-premise behavior target

- critical alerts go through Baileys path
- queued/retry behavior exists for on-prem mode

### Cloud behavior target

- critical alerts go through WhatsApp Cloud path

Code-level contract already in place:

- `get_notification_gateway()`
- same `send(destination, message, severity)` signature

Runtime validation target:

- execute one critical alert in on-prem mode and inspect gateway result/logs
- execute same code in cloud mode and verify cloud gateway path used

---

## K) Suggested validation sequence for reviewers

1. Run `setup.sh`
2. Login as Owner
3. Trigger `/api/analytics/run/<COMPANY_ID>`
4. Read `/api/owner/dashboard`
5. Read `/api/owner/dashboard/layer2`
6. Read `/api/owner/dashboard/layer3`
7. Pick one `document_id`
8. Read `/api/owner/dashboard/layer4/<DOCUMENT_ID>`
9. Login as Auditor and verify `403` on owner analytics
10. Login as Manager and verify scoped output only

---

## Current known Phase 3 caveats

These are the remaining important validation items:

- live frontend drill-down should be tested against running backend APIs
- real Baileys / WhatsApp Cloud delivery still needs full runtime proof
- manager isolation is improved but should still be validated with a richer multi-branch dataset
- Phase 3 should be run end-to-end in Docker to confirm OCR/analysis/alerts flow under real conditions
