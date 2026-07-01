# AuditCore — Phase 2: Auditor's Working World + Cryptographic Trust Layer

**Branch:** `auditcore/phase2-trust-layer`
**Date:** 2026-06-29

Two rules govern this phase absolutely:

1. **No OCR result ever auto-commits** without human certification.
2. **Nothing in `audit_ledger` is ever updated or deleted** — corrections are
   reverse entries, documented, and permanently visible next to the original.

## Acceptance criteria — all auto-tested

| #   | Criterion                                                                   | Test(s)  |
| --- | --------------------------------------------------------------------------- | -------- |
| 1   | Arabic invoice → OCR + color-flags; certify → ledger entry                  | 8 tests  |
| 2   | Auditor scope: tasks + cert queue never include out-of-scope company/branch | 4 tests  |
| 3   | After certifying, Auditor still cannot reach analytics                      | 3 tests  |
| 4   | Missing SLA → demerit within 15 minutes                                     | 7 tests  |
| 5   | `/owner/ledger/verify` clean=true, tampered=names entry                     | 6 tests  |
| 6   | Certification + onboarding render fully in ckb; trust copy in both          | 10 tests |

**Result:** `38 passed` on `test_phase2_acceptance.py`, **140 passed, 1 skipped** total.

## What's already in the scaffold (verified, not changed)

- OCR worker `process_ocr_document` — decrypts via `decrypt_bytes_to_memory`,
  Tesseract `lang='ara'`, pdf2image, color flags Green/Yellow/Red, target ~3s/page
- Certification API `/certification/next` + `/certification/{id}/certify` —
  scoped through `get_accessible_company_ids`, refuses certification if any
  Yellow/Red field is left empty
- Daily task engine — Celery-Beat at 08:00 Baghdad + 15-minute SLA sweep;
  SLAs OCR=4h, statements=24h, reversals=2h; demerits critical=3 / normal=1
- Immutable ledger — `SHA-256(previous_hash + deterministic_json(entry))`,
  `verify_ledger_integrity` walks the full chain
- Owner ledger UI with [التحقق من سلامة السلسلة] → "السجل سليم 100%"

## What Phase 2 added

### New: Reverse-entry mechanism (production correction path)

- **`append_reverse_entry(session, company_id, actor_user_id, target_entry_id, reason, correction_payload)`**
  in `backend/app/services/ledger.py` — appends a new ledger entry referencing
  the original by id; never modifies the original.
- **`POST /owner/ledger/reverse/{entry_id}`** endpoint — accepts `{reason, correction}`.
  Requires a non-empty `reason` (the documented justification).
- The original `tamper` endpoint is kept but explicitly documented as **TEST-ONLY**
  — it simulates what happens if a row is mutated directly, proving the chain
  detects it. In production, all corrections flow through `/reverse/{id}`.

### New: AuditorOnboarding component (bilingual trust framing)

- **`src/components/auditor-onboarding.tsx`** — bilingual card with the
  trust-framing copy exactly as the spec requires:
  - Greeting in both languages
  - "أنت الدور الأكثر ثقة تشغيلاً / تۆ متمانەپێوترین ڕۆڵی کارپێکردن" headline
  - ٪90 trust percentage in both languages (with Arabic-Indic ٩٠ for Sorani)
  - "Why don't I see analytics?" explanation — states plainly that the
    restriction protects the Auditor's own work, not distrust of them personally
  - <30 minute training target in both languages
  - "No auto-commit" guarantee in both languages
  - "Every certification is recorded forever" in both languages
- Shown on first login (localStorage dismiss), AND at the top of the
  certification screen (`force` prop) every session.

### Updated: Auditor UI pages

- **`src/routes/auditor.index.tsx`** — now uses `getLocale()` + locale-driven
  strings (ar/ckb). The certification button label, color-flag labels
  (أخضر/أصفر/أحمر / سەوز/زەرد/سوور), "no pending" message, and onboarding
  card are all bilingual.
- **`src/routes/auditor.tasks.tsx`** — bilingual status text,
  remaining/overdue/demerits labels, summary line, empty-state message.

### New i18n keys (backend)

- `auditor.onboarding.*` (8 keys × 2 languages): greeting, headline,
  trust_pct, why, explanation, training_target, no_auto_commit,
  irreversible, dismiss
- `certification.color_*`, `certify_button`, `certified_and_next`,
  `queue_empty`
- `ledger.reverse_*` (3 keys × 2 languages): reverse_created,
  reverse_reason_required, reverse_target_not_found
- `ledger.tamper_test_only` — explicit warning in both languages
- `tasks.*` (6 keys × 2 languages): title, subtitle, overdue,
  remaining_minutes, demerit_points, empty, summary

### Updated: Owner ledger endpoints

- `tamper` endpoint now returns a `note` field warning that this is
  test-only behavior — production corrections use `/reverse/{id}`.
- The ledger `/verify` endpoint behavior is unchanged: returns
  `(valid, message, broken_entry_id)` — true + Arabic/Sorani "intact"
  message on a clean chain, false + the exact broken entry id when tampered.

## Trust boundary proof

```
$ PYTHONPATH=backend python -m pytest backend/app/tests/test_phase2_acceptance.py

38 passed

$ PYTHONPATH=backend python -m pytest backend/app/tests/

140 passed, 1 skipped

$ bash scripts/check_no_external_ai.sh
✓ PASS
```

## How to verify end-to-end (with Docker)

```bash
./scripts/setup.sh
# 1. Login as auditor
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@auditcore.local","password":"Auditor123!"}' | jq -r .access_token)

# 2. Upload an Arabic invoice
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F company_id=<your-company-id> \
  -F file=@sample-arabic-invoice.pdf

# 3. Wait for OCR worker (3s/page target)
# 4. Fetch next certification
curl http://localhost:8000/api/certification/next?company_id=<id> \
  -H "Authorization: Bearer $TOKEN"

# 5. Correct yellow/red fields, certify
curl -X POST http://localhost:8000/api/certification/<id>/certify \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"fields":{"invoice_number":"INV-...","date":"2026-...","amount":"...","vendor_name":"...","items_list":["..."]}}'

# 6. Verify ledger (Owner only)
curl http://localhost:8000/api/owner/ledger/verify?company_id=<id> \
  -H "Authorization: Bearer <owner-token>"

# 7. Try a reverse entry (Owner)
curl -X POST http://localhost:8000/api/owner/ledger/reverse/<entry-id>?company_id=<id> \
  -H "Authorization: Bearer <owner-token>" \
  -H 'Content-Type: application/json' \
  -d '{"reason":"Wrong vendor name on INV-9001","correction":{"vendor_name":"الرافدين"}}'
```
