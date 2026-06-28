# Phase 2 acceptance checklist notes

- Upload Arabic invoice image/PDF -> encrypted at rest, OCR queued.
- Celery worker decrypts in memory only and updates OCR extraction.
- Auditor fetches `/api/certification/next`, corrects yellow/red fields, certifies.
- Ledger chain gets `document_uploaded`, `ocr_processed`, `document_certified`, `task_status_changed` entries.
- Auditor still blocked from analytics by PostgreSQL RLS.
- SLA demerits applied every 15 minutes after deadline.
- `/api/owner/ledger/verify` reports clean chain or exact broken entry id.
