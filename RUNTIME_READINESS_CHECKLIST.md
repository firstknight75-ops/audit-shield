# Runtime Readiness Checklist: Phases 1–4

## Purpose
This checklist is for a real Docker/Kubernetes-enabled environment to validate the platform end-to-end.

---

## Phase 1: Foundation readiness

### Infrastructure
- [ ] `docker compose up -d` starts successfully
- [ ] backend container healthy
- [ ] postgres healthy
- [ ] redis healthy
- [ ] celery worker healthy
- [ ] celery beat healthy
- [ ] frontend reachable

### Database / migrations
- [ ] `alembic upgrade head` completes cleanly
- [ ] all expected tables exist
- [ ] RLS enabled on:
  - [ ] `analytics_outputs`
  - [ ] `waste_map_items`
  - [ ] `risk_alerts`

### Auth / permissions
- [ ] all 6 seeded users can log in
- [ ] `/api/auth/me` returns distinct permission sets
- [ ] failed-login lockout works
- [ ] 15-minute inactivity logic behaves correctly

### Tenant isolation
- [ ] on-prem single-tenant path works
- [ ] cloud pooled schema tenant works
- [ ] cloud elite dedicated DB path works
- [ ] cross-tenant isolation test passes

---

## Phase 2: OCR / ledger readiness

### OCR
- [ ] image upload succeeds
- [ ] PDF upload succeeds
- [ ] fake renamed file is rejected
- [ ] OCR worker runs without dependency failure
- [ ] Tesseract Arabic OCR executes
- [ ] pdf2image path executes

### Certification
- [ ] `/api/certification/next` returns pending item
- [ ] low-confidence fields require correction
- [ ] certification creates ledger entry
- [ ] next item auto-flow works at API level

### Ledger
- [ ] `/api/owner/ledger/verify` returns valid on clean chain
- [ ] tamper test returns exact broken entry
- [ ] ledger trail remains append-only in workflow

### SLA engine
- [ ] task generation at 08:00 Baghdad time works
- [ ] overdue demerit applied within 15 minutes after deadline

---

## Phase 3: Analytics readiness

### Local AI execution
- [ ] no external AI/LLM calls in runtime
- [ ] analysis runs locally
- [ ] 10+ certified invoices can be analyzed
- [ ] duplicate invoice is flagged
- [ ] procurement/inventory mismatch is flagged
- [ ] waste map receives IQD amounts
- [ ] trust index generated
- [ ] predictor output generated
- [ ] Arabic narratives generated

### Dashboard isolation
- [ ] owner dashboard returns analytics
- [ ] auditor gets 403 on owner analytics endpoints
- [ ] manager sees scoped data only

### Alerts
- [ ] critical alert path uses correct gateway for on-prem
- [ ] critical alert path uses correct gateway for cloud
- [ ] queued retries run every 5 minutes
- [ ] DND behavior verified

---

## Phase 4: Productization readiness

### Manager dashboard
- [ ] manager widgets render
- [ ] widget scope remains isolated to branch/department

### Export engine
- [ ] Waste Map Excel opens in Arabic RTL correctly
- [ ] PDF renders correctly in Arabic
- [ ] PNG export produces usable image output
- [ ] export certificate contains hash and signature
- [ ] all 7 core outputs are exportable

### What-If simulator
- [ ] manual example matches hand calculation
- [ ] exported PDF renders correctly

### App Owner panel
- [ ] clients list populated from inventory only
- [ ] no tenant-schema joins used for listing
- [ ] tier change updates cap/features
- [ ] pooled → elite migration completes without data loss
- [ ] template create/push/rollback works
- [ ] CRaaS queue works
- [ ] maintenance log records actions
- [ ] App Owner still cannot read tenant analytics/financial content

### Ops
- [ ] `install.sh` gets to first login in <30 min
- [ ] `backup.sh` produces encrypted backup artifact
- [ ] `healthcheck.sh` produces expected health result
- [ ] `update.sh` backup-first flow works
- [ ] cloud deploy provisions tenant correctly
- [ ] pod/container stop triggers alert within 5 minutes

---

## Final go-live gate
- [ ] all API tests pass
- [ ] all phase tests pass
- [ ] no blocker errors in logs
- [ ] exports verified manually
- [ ] cross-tenant and auditor isolation re-verified
- [ ] rollback path documented and tested
