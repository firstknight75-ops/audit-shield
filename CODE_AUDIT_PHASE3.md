# Code Audit: Likely Runtime Breakpoints

## High risk

1. **Alembic async mismatch**

- `backend/alembic/env.py` uses sync `engine_from_config` with an asyncpg URL.
- Likely failure when running `alembic upgrade head` in a real environment.
- Fix: use Alembic async migration pattern or a sync driver for migrations.

2. **Celery task registration/import risk**

- `process_ocr_document.delay(...)` is called from API code, but Celery worker discovery may fail unless task modules are imported reliably on worker startup.
- `run_daily_analysis` is added in `backend/app/ai/orchestrator.py`, but beat scheduling assumes that file is imported before schedule usage matters.
- Fix: explicitly import worker/AI task modules in `app/core/celery_app.py`.

3. **Docker image missing OCR runtime dependencies**

- `backend/Dockerfile` installs `libmagic1` only.
- OCR stack likely needs system packages for:
  - `tesseract-ocr`
  - Arabic language pack
  - `poppler-utils` for pdf2image
- Without them, OCR worker will fail at runtime.

4. **RLS enforcement depends on session context timing**

- Protection relies on `set_session_context()` being called before sensitive queries.
- Any code path using DB session outside `get_current_user` can bypass intended role-setting behavior.
- Fix: centralize session role-setting more aggressively and audit all analytics query paths.

5. **Manager scope is still heuristic, not model-level**

- Current manager scoping filters findings by document IDs linked to branch documents.
- This is better than description matching, but still not a true department/branch analytic partition on all derived outputs.
- Fix: persist `branch_id` and `department` structurally on findings/analytics artifacts.

6. **`/analytics/run/{company_id}` can target arbitrary company ids**

- Permission check uses `view_analytics`, but route does not confirm requested `company_id == current_user.company_id`.
- In a multi-tenant cloud deployment this is a serious cross-tenant risk.
- Fix: hard-check `company_id` against authenticated tenant scope unless app-owner inventory flow explicitly allows otherwise.

## Medium risk

7. **Migration downgrade is empty**

- `downgrade()` is `pass`.
- This blocks rollback and makes failed deploy recovery harder.

8. **Notification queue table added to model + migration, but not yet used by a beat retry task**

- Queueing exists, flushing logic exists, but no periodic retry task is wired into Celery beat.
- Acceptance criterion mentions 5-minute retry on-prem.
- Fix: add periodic `flush_notification_queue` Celery task.

9. **Do-Not-Disturb logic may suppress critical alerts unexpectedly**

- Current `should_send_now()` returns immediate send for critical only if not in DND window.
- Acceptance may expect critical immediate push regardless, or a clearly defined override policy.
- Needs product confirmation and explicit behavior.

10. **Owner dashboard routing naming mismatch**

- Backend owner dashboard routes live under analytics router but exposed as `/api/owner/dashboard...` paths.
- Fine technically, but easy to confuse maintainers because owner analytics are not colocated with `owner.py`.

11. **Frontend still mostly mock-backed**

- Owner/manager drill-down screens are UI scaffolds using mock data.
- Acceptance requiring true drill-down to original invoice image is not fully satisfied until wired to live endpoints.

12. **Seed data may not satisfy every analytical path deterministically**

- Seed adds duplicate and mismatch patterns, but impact amounts and branch attribution may not fully line up with all drill-down expectations every time unless analysis is actually executed post-seed.

13. **`python-magic` MIME behavior varies by environment**

- File validation may behave differently across base images/OS packages.
- Needs live environment verification.

## Lower risk but important

14. **`waste_map_items` schema lacks explicit IQD amount field**

- Acceptance asks for populated waste map items with real IQD figures.
- Current AI logic computes IQD internally, but DB model stores only category/description/impact_score.
- Fix: add `iqd_amount` column.

15. **`risk_alerts` lacks routing metadata**

- Could benefit from channel/delivery_state fields for proving notification outcomes.

16. **On-prem/cloud notification gateways are stubs**

- Same call signature exists, good.
- But no real Baileys or WhatsApp Cloud delivery implementation yet.
- Acceptance calling for delivery in both test instances is not yet fully met.

17. **Ledger layer-4 trace filtering is substring-based**

- `document_id in str(r.action_payload)` is fragile.
- Fix: structured lookup on payload keys.

18. **Cloud elite dedicated DB path remains incomplete**

- Prior phases mention it, but actual per-tenant DB provisioning + switching still looks scaffolded.

## Recommended next fixes, in order

1. Fix Alembic async migration path.
2. Add OCR system packages to Dockerfile.
3. Explicitly register/import Celery tasks.
4. Restrict `/analytics/run/{company_id}` to current tenant/company.
5. Add `iqd_amount` to `waste_map_items`.
6. Add periodic notification-queue flush task.
7. Replace ledger trace substring matching with structured payload filtering.
8. Wire owner/manager dashboards to live backend APIs.
9. Strengthen manager scoping with explicit branch/department fields on generated outputs.
10. Run full Docker integration validation.

## Fast acceptance-gap summary

Not yet fully proven in code/runtime:

- critical alert delivery through real Baileys and real WhatsApp Cloud using the same production code path
- full owner live drill-down to actual stored original invoice image via frontend
- full manager multi-department isolation proof in a live seeded company
- live 10+ certified invoices -> waste map IQD population proven through executed analysis run
