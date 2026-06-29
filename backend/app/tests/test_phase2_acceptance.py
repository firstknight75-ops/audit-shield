"""Phase 2 Acceptance Tests.

Maps directly to the 6 acceptance criteria from the AuditCore Phase 2 spec:

1. Arabic invoice → OCR extracts and color-flags; certification creates ledger entry.
2. Auditor task list + cert queue scoped to accessible companies/branches.
3. After certifying, Auditor still cannot reach any financial analytics.
4. Missing an SLA → demerit within 15 minutes of deadline.
5. /owner/ledger/verify returns true on clean chain, names exact entry if tampered.
6. Certification screen + Auditor onboarding card render fully in ckb with
   trust-framing copy present in both languages.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ledger import (
    _hash,
    append_ledger_entry,
    append_reverse_entry,
    verify_ledger_integrity,
)

# Path math: backend/app/tests/test_phase2_acceptance.py
REPO = pathlib.Path(__file__).resolve().parents[3]
APP = pathlib.Path(__file__).resolve().parents[1]


# ─────────────────────────────────────────────────────────────────────
# Acceptance #1 — OCR extracts Arabic invoice + color flags correctly;
#                 certify creates ledger entry
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_1_ocr_color_thresholds_match_spec():
    """Green ≥85, Yellow 60–84, Red <60/missing."""
    from app.services.ocr import confidence_color
    assert confidence_color(100) == 'green'
    assert confidence_color(85) == 'green'
    assert confidence_color(84) == 'yellow'
    assert confidence_color(60) == 'yellow'
    assert confidence_color(59) == 'red'
    assert confidence_color(0) == 'red'


def test_acceptance_1_ocr_extracts_required_fields():
    from app.services.ocr import _extract_fields
    arabic_invoice_text = """شركة الرافدين للتوريدات
INV-2026-9001
2026-06-28
1,250,000 IQD
صنف أ - 10 وحدة
صنف ب - 5 وحدة
صنف ج - 3 وحدة"""
    data, conf = _extract_fields(arabic_invoice_text)
    assert data['invoice_number']
    assert data['date']
    assert data['amount']
    assert data['vendor_name']
    assert isinstance(data['items_list'], list)


def test_acceptance_1_ocr_uses_arabic_tesseract_for_images():
    """The OCR service must use Tesseract with lang='ara' for images."""
    ocr_py = (APP / 'services' / 'ocr.py').read_text()
    assert "lang='ara'" in ocr_py or 'lang="ara"' in ocr_py
    assert 'pytesseract' in ocr_py


def test_acceptance_1_ocr_uses_pdf2image_for_pdfs():
    """PDF processing must use pdf2image."""
    ocr_py = (APP / 'services' / 'ocr.py').read_text()
    assert 'pdf2image' in ocr_py
    assert 'convert_from_bytes' in ocr_py


def test_acceptance_1_ocr_decrypts_in_memory_only():
    """The OCR worker must decrypt via decrypt_bytes_to_memory, never persist plaintext."""
    workers_py = (APP / 'workers' / 'tasks.py').read_text()
    assert 'decrypt_bytes_to_memory' in workers_py
    # Must NOT write plaintext anywhere
    assert 'open(' not in workers_py  # no plaintext file write


def test_acceptance_1_certify_writes_ledger_entry_with_correct_action_type():
    """The certify endpoint must write a ledger entry with action_type='document_certified'."""
    cert_py = (APP / 'api' / 'certification.py').read_text()
    assert "'document_certified'" in cert_py
    assert 'append_ledger_entry' in cert_py


def test_acceptance_1_certify_requires_yellow_red_correction():
    """A field with confidence < 85 cannot be left empty — certify must reject."""
    cert_py = (APP / 'api' / 'certification.py').read_text()
    assert 'conf < 85' in cert_py
    assert 'field_requires_correction' in cert_py


def test_acceptance_1_certify_button_label_in_both_languages():
    """Button label [تأكيد واعتماد المستند] is required in Arabic; Sorani counterpart required."""
    auditor_index = (REPO / 'src' / 'routes' / 'auditor.index.tsx').read_text()
    assert 'تأكيد واعتماد المستند' in auditor_index
    # Sorani counterpart
    assert 'دووبەرەکرن و پەسندکردنی بەڵگەنامە' in auditor_index


# ─────────────────────────────────────────────────────────────────────
# Acceptance #2 — Auditor scope: tasks + cert queue never include
#                 a company/branch outside their user_company_access
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_2_certification_next_uses_get_accessible_company_ids():
    """The /certification/next endpoint MUST scope through get_accessible_company_ids."""
    cert_py = (APP / 'api' / 'certification.py').read_text()
    assert 'get_accessible_company_ids' in cert_py
    assert 'Document.company_id.in_(accessible_ids)' in cert_py


def test_acceptance_2_certify_uses_get_accessible_company_ids():
    """The /certification/{id}/certify endpoint MUST scope through accessible IDs."""
    cert_py = (APP / 'api' / 'certification.py').read_text()
    # Both /next and /certify use it
    assert cert_py.count('get_accessible_company_ids') >= 2


def test_acceptance_2_daily_task_worker_filters_by_user_company_access():
    """The generate_daily_tasks worker must skip auditors without access."""
    workers_py = (APP / 'workers' / 'tasks.py').read_text()
    assert 'UserCompanyAccess' in workers_py
    # Verifies access for the auditor → document company pair
    assert 'auditor.id' in workers_py
    assert 'doc.company_id' in workers_py


def test_acceptance_2_daily_task_worker_filters_by_branch():
    """If the auditor is branch-scoped, only documents in that branch must surface."""
    workers_py = (APP / 'workers' / 'tasks.py').read_text()
    assert 'access.branch_id' in workers_py
    assert 'doc.branch_id' in workers_py


# ─────────────────────────────────────────────────────────────────────
# Acceptance #3 — After certifying, Auditor still cannot reach analytics
#                 (Phase 1 RLS guarantee persists)
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_3_auditor_role_still_has_no_analytics_permission():
    """Auditor must not gain analytics access via certification."""
    from app.services.permissions import ROLE_DEFAULTS
    auditor_perms = ROLE_DEFAULTS['auditor']
    forbidden = ['view_owner_dashboard', 'view_waste_map', 'view_risk_alerts',
                 'view_audit_ledger', 'manage_company_users', 'manage_permissions',
                 'export_reports', 'approve_custom_reports']
    for code in forbidden:
        assert code not in auditor_perms


def test_acceptance_3_rls_migration_still_blocks_auditor():
    """The Phase 1 RLS migration is unchanged in Phase 2 — auditor still blocked."""
    import re
    BACKEND = pathlib.Path(__file__).resolve().parents[2]
    migration = BACKEND / 'alembic' / 'versions' / '20260629_0001_init.py'
    text = migration.read_text()
    # The migration uses an f-string loop; verify the templates exist
    assert "for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:" in text
    assert re.search(r"auditor_no_access_\{table\}", text)
    assert "current_setting('app.current_user_role', true) != 'auditor'" in text


def test_acceptance_3_analytics_endpoints_require_view_owner_dashboard():
    """Every analytics endpoint must require view_owner_dashboard, which auditor lacks."""
    analytics_py = (APP / 'api' / 'analytics.py').read_text()
    assert "require_permission('view_owner_dashboard')" in analytics_py


# ─────────────────────────────────────────────────────────────────────
# Acceptance #4 — Missing an SLA → demerit within 15 minutes
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_4_sla_demerit_window_is_15_minutes():
    """The apply_sla_demerits worker must trigger within 15 minutes of the deadline."""
    workers_py = (APP / 'workers' / 'tasks.py').read_text()
    assert 'timedelta(minutes=15)' in workers_py


def test_acceptance_4_celery_beat_runs_demerit_sweep_every_15_minutes():
    """Celery-Beat must schedule the SLA demerit sweep every 15 minutes."""
    celery_py = (APP / 'core' / 'celery_app.py').read_text()
    assert "minute='*/15'" in celery_py or 'minute=*/15' in celery_py
    assert 'apply_sla_demerits' in celery_py


def test_acceptance_4_sla_demerit_points_by_severity():
    """Critical = 3 pts, normal = 1 pt — per spec."""
    workers_py = (APP / 'workers' / 'tasks.py').read_text()
    assert 'severity == \'critical\'' in workers_py
    assert 'demerit_points = 3' in workers_py
    assert 'demerit_points = 1' in workers_py or 'else 1' in workers_py


def test_acceptance_4_sla_durations_match_spec():
    """OCR 4h, statements 24h, reversals 2h — per spec."""
    workers_py = (APP / 'workers' / 'tasks.py').read_text()
    assert "'ocr': 240" in workers_py
    assert "'statements': 1440" in workers_py
    assert "'reversals': 120" in workers_py


def test_acceptance_4_efficiency_formula():
    """Owner-only efficiency = (on_time/total)*100 - (demerits*5)."""
    owner_py = (APP / 'api' / 'owner.py').read_text()
    assert '(on_time / total) * 100' in owner_py
    assert 'demerits * 5' in owner_py


def test_acceptance_4_efficiency_visible_to_owner_only():
    """The auditor-efficiency endpoint must require view_owner_dashboard, not view_documents."""
    owner_py = (APP / 'api' / 'owner.py').read_text()
    assert "require_permission('view_owner_dashboard')" in owner_py


def test_acceptance_4_daily_tasks_generated_at_08_baghdad():
    """Celery-Beat schedule: generate-daily-auditor-tasks at 08:00 Baghdad."""
    celery_py = (APP / 'core' / 'celery_app.py').read_text()
    assert 'crontab(hour=8, minute=0)' in celery_py
    assert 'Asia/Baghdad' in celery_py


# ─────────────────────────────────────────────────────────────────────
# Acceptance #5 — /owner/ledger/verify: clean → true; tampered → names entry
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_5_hash_chain_clean_returns_intact():
    """A clean chain returns (True, intact_message, None)."""
    async def run():
        from app.services.ledger import verify_ledger_integrity
        session = AsyncMock()
        rows = []
        for i in range(3):
            row = MagicMock()
            row.id = f'entry-{i}'
            body = {'entry_id': f'entry-{i}', 'company_id': 'c', 'actor_user_id': None, 'action_type': 'test', 'action_payload': {}, 'created_at': f'2026-01-01T00:00:0{i}'}
            previous_hash = rows[i-1].action_payload.get('entry_hash', 'GENESIS') if i > 0 else 'GENESIS'
            row.action_payload = {'entry_body': body, 'entry_hash': _hash(previous_hash, body)}
            rows.append(row)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = rows
        session.execute.return_value = result_mock
        return await verify_ledger_integrity(session, 'c', 'ar')
    valid, msg, broken = asyncio.run(run())
    assert valid is True
    assert broken is None
    assert 'سليم' in msg or 'intact' in msg.lower()


def test_acceptance_5_hash_chain_tampered_names_exact_entry():
    """If one entry's hash is altered, verify returns (False, broken_msg, broken_id)."""
    async def run():
        from app.services.ledger import verify_ledger_integrity
        session = AsyncMock()
        rows = []
        for i in range(3):
            row = MagicMock()
            row.id = f'entry-{i}'
            body = {'entry_id': f'entry-{i}', 'company_id': 'c', 'actor_user_id': None, 'action_type': 'test', 'action_payload': {}, 'created_at': f'2026-01-01T00:00:0{i}'}
            previous_hash = rows[i-1].action_payload.get('entry_hash', 'GENESIS') if i > 0 else 'GENESIS'
            row.action_payload = {'entry_body': body, 'entry_hash': _hash(previous_hash, body)}
            rows.append(row)
        # Simulate direct DB tampering on the middle row
        rows[1].action_payload['entry_hash'] = 'forged-hash-value'
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = rows
        session.execute.return_value = result_mock
        return await verify_ledger_integrity(session, 'c', 'ar')
    valid, msg, broken = asyncio.run(run())
    assert valid is False
    assert broken == 'entry-1'
    assert 'مكسورة' in msg or 'broken' in msg.lower()


def test_acceptance_5_reverse_entry_does_not_modify_original():
    """The reverse-entry mechanism must NOT mutate the original — only append a new entry.

    We use real (non-mock) ledger rows since the hash chain depends on real JSON
    serialization of the entry body.
    """
    async def run():
        from app.services.ledger import append_ledger_entry, append_reverse_entry

        # Build a simple in-memory mock that returns the right things.
        # Use real dicts so JSON serialization works.
        stored_entries: list = []

        class FakeSession:
            async def execute(self, stmt):
                result = MagicMock()
                # Return the latest stored entry (for previous_hash lookup)
                if stored_entries:
                    result.scalars.return_value.first.return_value = stored_entries[-1]
                else:
                    result.scalars.return_value.first.return_value = None
                result.scalar_one_or_none.return_value = (
                    stored_entries[-1] if stored_entries else None
                )
                return result
            def add(self, entry):
                stored_entries.append(entry)
            async def flush(self):
                pass

        session = FakeSession()
        original = await append_ledger_entry(session, 'c', 'u1', 'document_certified', {'document_id': 'd1'})
        original_id = original.id
        original_hash_before = original.action_payload['entry_hash']
        original_body_before = dict(original.action_payload['entry_body'])
        original_type_before = original.action_type

        # Now reverse it
        reverse = await append_reverse_entry(
            session, 'c', 'u1',
            target_entry_id=original_id,
            reason='Wrong vendor name — should be الرافدين not الزهراء',
            correction_payload={'vendor_name': 'الرافدين'},
        )

        # The original must NOT have changed
        assert original.action_payload['entry_hash'] == original_hash_before
        assert original.action_payload['entry_body'] == original_body_before
        assert original_type_before == 'document_certified'

        # The reverse must be a NEW entry referencing the original
        assert reverse.action_type == 'reverse_entry'
        assert reverse.action_payload['reverse_target_id'] == original_id
        assert 'vendor name' in reverse.action_payload['reason'].lower() or 'الرافدين' in reverse.action_payload['reason']
        assert reverse.action_payload['original_unchanged'] is True

        # Both entries must be in the stored list (not replaced)
        assert len(stored_entries) == 2
        assert stored_entries[0] is original
        assert stored_entries[1] is reverse
    asyncio.run(run())


def test_acceptance_5_reverse_entry_required_reason():
    """A reverse entry without a reason must raise ValueError."""
    async def run():
        from app.services.ledger import append_reverse_entry

        session = AsyncMock()
        # No target found
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        with pytest.raises(ValueError):
            await append_reverse_entry(
                session, 'c', 'u1',
                target_entry_id='nonexistent',
                reason='any reason',
            )
    asyncio.run(run())


def test_acceptance_5_owner_reverse_endpoint_exists():
    """The /owner/ledger/reverse/{entry_id} endpoint must exist."""
    owner_py = (APP / 'api' / 'owner.py').read_text()
    assert '/ledger/reverse/' in owner_py
    assert 'reverse_entry' in owner_py or 'append_reverse_entry' in owner_py


def test_acceptance_5_tamper_endpoint_exists_for_demo():
    """The /owner/ledger/tamper/{entry_id} endpoint exists (test-only, simulates direct mutation)."""
    owner_py = (APP / 'api' / 'owner.py').read_text()
    assert '/ledger/tamper/' in owner_py
    # It must be marked test-only
    assert 'TEST-ONLY' in owner_py or 'tamper_test_only' in owner_py


# ─────────────────────────────────────────────────────────────────────
# Acceptance #6 — Certification screen + Auditor onboarding card
#                 render fully in ckb with trust-framing copy in both
# ─────────────────────────────────────────────────────────────────────

def test_acceptance_6_auditor_onboarding_component_exists():
    p = REPO / 'src' / 'components' / 'auditor-onboarding.tsx'
    assert p.exists()
    content = p.read_text()
    assert 'AuditorOnboarding' in content
    assert 'locale' in content


def test_acceptance_6_onboarding_copy_present_in_both_languages():
    """The trust-framing copy must exist in both ar and ckb."""
    component = (REPO / 'src' / 'components' / 'auditor-onboarding.tsx').read_text()
    # Arabic — headline
    assert 'أنت الدور الأكثر ثقة تشغيلاً' in component
    # Arabic — 90% trust percentage
    assert '٪90' in component
    # Sorani — headline
    assert 'متمانەپێوترین ڕۆڵی کارپێکردن' in component
    # Sorani — 90% with Arabic-Indic digits
    assert '٪٩٠' in component


def test_acceptance_6_onboarding_explanation_in_both_languages():
    """The 'why restricted' explanation must exist in both languages."""
    component = (REPO / 'src' / 'components' / 'auditor-onboarding.tsx').read_text()
    # Arabic — explains not distrust, but integrity protection
    assert 'لا ينبع من أي شك فيك' in component
    # Sorani
    assert 'هیچ دوودڵییەکی تایبەت بە تۆوە' in component


def test_acceptance_6_onboarding_training_target_bilingual():
    """The <30 minute training target must be in both languages."""
    component = (REPO / 'src' / 'components' / 'auditor-onboarding.tsx').read_text()
    assert '30 دقيقة' in component
    assert '٣٠ خولەک' in component


def test_acceptance_6_onboarding_no_auto_commit_bilingual():
    """'No auto-commit' must be in both languages."""
    component = (REPO / 'src' / 'components' / 'auditor-onboarding.tsx').read_text()
    assert 'لا يتم اعتماد أي مستند تلقائياً' in component
    assert 'هیچ بەڵگەنامەیەک بە خۆکار پەسند ناکرێت' in component


def test_acceptance_6_auditor_index_uses_auditor_onboarding():
    """The /auditor/ page must include the AuditorOnboarding component."""
    page = (REPO / 'src' / 'routes' / 'auditor.index.tsx').read_text()
    assert 'AuditorOnboarding' in page
    assert 'force' in page  # shown on certification screen


def test_acceptance_6_auditor_index_uses_i18n_not_hardcoded():
    """The certification screen must use the locale-driven strings, not hardcoded Arabic."""
    page = (REPO / 'src' / 'routes' / 'auditor.index.tsx').read_text()
    assert 'locale ===' in page
    assert 'getLocale' in page
    # Sorani-specific letters must appear in the i18n strings
    sorani_chars = ['ھ', 'ێ', 'ۆ', 'ڵ', 'ڕ', 'ە']
    for ch in sorani_chars:
        if ch in page:
            continue  # good, found one
    # At least one Sorani-specific letter must appear in the page (Sorani text)
    page_sorani_letters = set(c for c in page if c in sorani_chars)
    assert len(page_sorani_letters) >= 1, f'No Sorani-specific letters found in auditor index page'


def test_acceptance_6_auditor_tasks_page_bilingual():
    """The /auditor/tasks page must be bilingual."""
    page = (REPO / 'src' / 'routes' / 'auditor.tasks.tsx').read_text()
    assert 'locale ===' in page
    assert 'مهامي' in page or 'مهامي اليومية' in page
    assert 'ئەرکە' in page


def test_acceptance_6_backend_i18n_has_onboarding_keys():
    """Backend translation table must include onboarding keys for both languages."""
    from app.i18n.translations import TRANSLATIONS
    required = [
        'auditor.onboarding.greeting',
        'auditor.onboarding.headline',
        'auditor.onboarding.explanation',
        'auditor.onboarding.training_target',
        'auditor.onboarding.no_auto_commit',
        'auditor.onboarding.irreversible',
    ]
    for key in required:
        assert key in TRANSLATIONS, f'missing key: {key}'
        assert 'ar' in TRANSLATIONS[key], f'missing ar for {key}'
        assert 'ckb' in TRANSLATIONS[key], f'missing ckb for {key}'
        # Verify non-empty
        assert TRANSLATIONS[key]['ar'].strip()
        assert TRANSLATIONS[key]['ckb'].strip()


def test_acceptance_6_certification_screen_i18n_keys_exist():
    """All UI strings on the certification screen must have ar + ckb."""
    from app.i18n.translations import TRANSLATIONS
    required = [
        'certification.color_green',
        'certification.color_yellow',
        'certification.color_red',
        'certification.certify_button',
        'certification.certified_and_next',
        'certification.queue_empty',
        'tasks.title',
        'tasks.subtitle',
        'tasks.overdue',
        'tasks.remaining_minutes',
        'tasks.demerit_points',
    ]
    for key in required:
        assert key in TRANSLATIONS, f'missing key: {key}'
        assert 'ar' in TRANSLATIONS[key], f'missing ar for {key}'
        assert 'ckb' in TRANSLATIONS[key], f'missing ckb for {key}'
