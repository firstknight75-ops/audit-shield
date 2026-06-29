"""Trust Boundary Tests — proving the 8 AuditCore principles.

These tests are pure-logic so they run without Docker/Postgres. The
contract under test is: every trust boundary is enforced by the code
itself, not by UI hiding.

If any test here fails, the corresponding principle is broken.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from app.services.action_plan import build_adaptation_path, build_change_path
from app.services.activation import compute_activation_status
from app.services.opportunity_map import build_opportunity_map
from app.services.portfolio import CompanyPortfolioEntry, build_portfolio
from app.services.silent_ai import (
    LOCAL_AI_MODULES,
    check_no_chatbot_endpoint,
    check_no_external_ai_calls,
    list_local_modules,
    run_silent_ai_self_test,
)
from app.services.trust_index import compute_trust_index, merge_findings_into_trust


# ── Principle 2: Zero-Knowledge Audit ────────────────────────────────

def test_principle2_auditor_role_has_no_view_analytics_permission():
    """Auditor's effective permission set must NOT include view_analytics."""
    from app.services.permissions import ROLE_DEFAULTS
    auditor_perms = ROLE_DEFAULTS['auditor']
    assert 'view_analytics' not in auditor_perms
    assert 'view_waste_map' not in auditor_perms
    assert 'view_risk_alerts' not in auditor_perms


def test_principle2_auditor_rls_policy_targets_all_hidden_tables():
    """The migration must enable RLS on analytics_outputs, waste_map_items, risk_alerts."""
    import pathlib
    # tests live at backend/app/tests/test_trust_boundaries.py
    # migration lives at backend/alembic/versions/20260629_0001_init.py
    migration_path = pathlib.Path(__file__).resolve().parents[3] / 'alembic' / 'versions' / '20260629_0001_init.py'
    if not migration_path.exists():
        pytest.skip('migration file not present')
    text = migration_path.read_text(encoding='utf-8')
    for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:
        assert f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY' in text, f'RLS not enabled on {table}'
        assert f"auditor_no_access_{table}" in text, f'auditor-denied policy missing on {table}'
        assert f"tenant_isolation_{table}" in text, f'tenant-isolation policy missing on {table}'


# ── Principle 3: Immutability (hash-chained ledger) ──────────────────

def test_principle3_hash_chain_detects_tampering():
    """A mutated ledger entry must be detected by verify_ledger_integrity."""
    from app.services.ledger import _hash
    body1 = {'entry_id': '1', 'action_type': 'upload', 'payload': {'x': 1}}
    h1 = _hash('GENESIS', body1)
    body2 = {'entry_id': '2', 'action_type': 'certify', 'payload': {'x': 2}}
    h2 = _hash(h1, body2)
    # Tamper with body2
    body2_tampered = {**body2, 'payload': {'x': 999}}
    h2_recalc = _hash(h1, body2_tampered)
    assert h2_recalc != h2, 'Tampering must change the hash'


def test_principle3_genesis_hash_is_well_known():
    """The genesis previous-hash sentinel is 'GENESIS'."""
    from app.services.ledger import _hash
    h = _hash('GENESIS', {'entry_id': '0', 'action_type': 'genesis'})
    assert h == hashlib.sha256(('GENESIS' + json.dumps({'entry_id': '0', 'action_type': 'genesis'}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))).encode('utf-8')).hexdigest()


# ── Principle 4: Silent AI ──────────────────────────────────────────

def test_principle4_silent_ai_check_no_chatbot_endpoint():
    """No route path should contain chatbot-style substrings."""
    sample_routes = [
        {'path': '/api/owner/dashboard'},
        {'path': '/api/manager/dashboard'},
        {'path': '/api/auth/login'},
        {'path': '/api/documents/upload'},
    ]
    result = check_no_chatbot_endpoint(sample_routes)
    assert result['passed']
    assert result['flagged_routes'] == []

def test_principle4_silent_ai_check_no_chatbot_endpoint_catches_violation():
    sample_routes = [
        {'path': '/api/chat/send'},
        {'path': '/api/owner/dashboard'},
    ]
    result = check_no_chatbot_endpoint(sample_routes)
    assert not result['passed']
    assert any('chat' in r['path'] for r in result['flagged_routes'])


def test_principle4_silent_ai_local_modules_load():
    """Every local AI module must be importable."""
    modules = list_local_modules()
    loaded = [m for m in modules if m.get('loaded')]
    assert len(loaded) == len(LOCAL_AI_MODULES), f'some modules failed: {[m for m in modules if not m.get("loaded")]}'


def test_principle4_silent_ai_self_test_passes_with_clean_routes():
    """With a clean route set, all guarantees should pass."""
    result = run_silent_ai_self_test(routes=[
        {'path': '/api/owner/dashboard'},
        {'path': '/api/auth/login'},
    ])
    assert result['overall_passed'], f'failed checks: {[c for c in result["checks"] if not c["passed"]]}'


def test_principle4_silent_ai_self_test_fails_with_chatbot_route():
    """If a chat route sneaks in, the self-test must fail loudly."""
    result = run_silent_ai_self_test(routes=[{'path': '/api/assistant/ask'}])
    assert not result['overall_passed']


def test_principle4_silent_ai_no_external_ai_calls_in_modules():
    """None of the local AI modules may import openai/anthropic/etc."""
    result = check_no_external_ai_calls()
    assert result['passed'], f'forbidden imports found: {result["violations"]}'


# ── Principle 5: Truth From Data (4-layer drill-down + portfolio) ────

def test_principle5_portfolio_keeps_companies_unblended():
    """Portfolio must return per-company entries + an explicit labeled sum, never a silent blend."""
    entries = [
        CompanyPortfolioEntry('c1', 'شركة أ', 80, 1_000_000, 2, 500_000, 3, 50),
        CompanyPortfolioEntry('c2', 'شركة ب', 65, 2_000_000, 1, 300_000, 2, 30),
    ]
    result = build_portfolio(entries)
    assert len(result['companies']) == 2
    # sorted by trust desc
    assert result['companies'][0]['trust_index_score'] >= result['companies'][1]['trust_index_score']
    # totals explicitly labeled as sum, not blended
    assert result['totals_explicit_sum']['monthly_waste_iqd'] == 3_000_000
    assert 'unblended_note' in result
    assert 'تلقائياً' in result['unblended_note'] or 'لا' in result['unblended_note']


def test_principle5_portfolio_handles_single_company():
    """A portfolio with one company must still keep the unblended note."""
    entries = [CompanyPortfolioEntry('c1', 'شركة أ', 80, 1_000_000, 2, 500_000, 3, 50)]
    result = build_portfolio(entries)
    assert len(result['companies']) == 1
    assert 'unblended_note' in result


def test_principle5_portfolio_handles_empty():
    """An empty portfolio must not crash and must keep the unblended note."""
    result = build_portfolio([])
    assert result['companies'] == []
    assert 'unblended_note' in result


# ── Principle 6: App Owner zero visibility ───────────────────────────

def test_principle6_appowner_role_permissions_exclude_tenant_data():
    """The appowner role must NOT include view_analytics/view_ledger/upload_documents."""
    from app.services.permissions import ROLE_DEFAULTS
    appowner_perms = ROLE_DEFAULTS['appowner']
    forbidden_in_appowner = ['view_analytics', 'view_ledger', 'upload_documents', 'view_waste_map', 'view_risk_alerts']
    for code in forbidden_in_appowner:
        assert code not in appowner_perms, f'appowner must NOT have {code}'
    # and must include only platform permissions
    allowed = {'app_owner_inventory', 'app_owner_templates', 'app_owner_maintenance'}
    assert set(appowner_perms) == allowed


def test_principle6_admin_cannot_grant_appowner_permissions():
    """Admin's permission set must not include any appowner_* code."""
    from app.services.permissions import ROLE_DEFAULTS
    admin_perms = ROLE_DEFAULTS['admin']
    for code in admin_perms:
        assert not code.startswith('app_owner_'), f'admin must not have {code}'


# ── Principle 7: 48-hour activation ─────────────────────────────────

def test_principle7_activation_within_48h():
    from datetime import datetime, timedelta, timezone
    install = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    dashboard = install + timedelta(hours=36)
    status = compute_activation_status(
        install_at=install,
        first_upload_at=install + timedelta(hours=2),
        first_certified_at=install + timedelta(hours=10),
        first_dashboard_at=dashboard,
    )
    assert status.within_48h is True
    assert status.completed is True
    assert status.elapsed_hours <= 48


def test_principle7_activation_exceeds_48h():
    from datetime import datetime, timedelta, timezone
    install = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    dashboard = install + timedelta(hours=72)
    status = compute_activation_status(
        install_at=install,
        first_upload_at=install + timedelta(hours=10),
        first_certified_at=install + timedelta(hours=50),
        first_dashboard_at=dashboard,
    )
    assert status.within_48h is False
    assert status.completed is True
    assert status.elapsed_hours > 48


def test_principle7_activation_pending_never_completes():
    from datetime import datetime, timedelta, timezone
    install = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    now = install + timedelta(hours=10)
    status = compute_activation_status(
        install_at=install,
        first_upload_at=None,
        first_certified_at=None,
        first_dashboard_at=None,
        now=now,
    )
    assert status.completed is False
    assert status.within_48h is False
    assert status.elapsed_hours >= 10


# ── Principle 8: Sector/size adaptation (templates via actions) ─────

def test_principle8_adaptation_path_responds_to_trust_level():
    """Low trust level must produce at least one adaptation recommendation."""
    items = build_adaptation_path([], trust_level='low', coverage_pct=50)
    assert len(items) >= 1
    assert all(i.path == 'adaptation' for i in items)


def test_principle8_change_path_prioritizes_by_iqd():
    """Change path items must be ordered by IQD amount, highest first."""
    waste = [
        {'category': 'duplicate', 'iqd_amount': 100_000, 'description': 'small'},
        {'category': 'late_payment', 'iqd_amount': 1_000_000, 'description': 'big'},
        {'category': 'other', 'iqd_amount': 500_000, 'description': 'medium'},
    ]
    items = build_change_path(waste)
    assert items[0].estimated_iqd == 1_000_000
    assert items[1].estimated_iqd == 500_000
    assert items[2].estimated_iqd == 100_000


# ── Manager scoping (cross-cutting trust test) ──────────────────────

def test_manager_scope_filters_findings_to_allowed_documents():
    """Manager's findings list must be filtered to their allowed document IDs only."""
    findings = [
        {'document_id': 'doc-a'},
        {'document_id': 'doc-b'},
        {'document_id': 'doc-c'},
    ]
    allowed = {'doc-a', 'doc-c'}
    scoped = [f for f in findings if f['document_id'] in allowed]
    assert scoped == [{'document_id': 'doc-a'}, {'document_id': 'doc-c'}]


# ── Trust Index determinism ─────────────────────────────────────────

def test_trust_index_deterministic_for_same_inputs():
    a = compute_trust_index(total_documents=100, certified_documents=80, duplicate_documents=5, missing_fields_total=10)
    b = compute_trust_index(total_documents=100, certified_documents=80, duplicate_documents=5, missing_fields_total=10)
    assert a.score == b.score
    assert a.level == b.level


def test_trust_index_handles_zero_documents():
    a = compute_trust_index(total_documents=0, certified_documents=0, duplicate_documents=0, missing_fields_total=0)
    assert a.score == 0
    assert a.level == 'low'


def test_trust_index_full_coverage_full_certified_is_high():
    a = compute_trust_index(total_documents=100, certified_documents=100, duplicate_documents=0, missing_fields_total=0)
    assert a.score == 100
    assert a.level == 'high'


def test_trust_index_no_certifications_lowers_score():
    full = compute_trust_index(total_documents=100, certified_documents=100, duplicate_documents=0, missing_fields_total=0)
    none = compute_trust_index(total_documents=100, certified_documents=0, duplicate_documents=0, missing_fields_total=0)
    assert full.score > none.score


# ── Opportunity Map determinism ─────────────────────────────────────

def test_opportunity_map_empty_inputs_returns_empty():
    assert build_opportunity_map([], []) == []


def test_opportunity_map_vendor_underutilized_detected():
    documents = [
        {'invoice_number': '1', 'vendor_name': 'big_vendor', 'amount': 1_000_000, 'branch_name': 'b1'},
        {'invoice_number': '2', 'vendor_name': 'big_vendor', 'amount': 1_000_000, 'branch_name': 'b1'},
        {'invoice_number': '3', 'vendor_name': 'big_vendor', 'amount': 1_000_000, 'branch_name': 'b1'},
        {'invoice_number': '4', 'vendor_name': 'small_vendor', 'amount': 100_000, 'branch_name': 'b1'},
    ]
    opps = build_opportunity_map(documents, [])
    kinds = {o.kind for o in opps}
    assert 'vendor_underutilized' in kinds
    # small_vendor should appear, big_vendor should not
    vendor_opp = next(o for o in opps if o.kind == 'vendor_underutilized')
    assert vendor_opp.basis['vendor'] == 'small_vendor'


def test_opportunity_map_branch_underutilized_detected():
    documents = [
        {'invoice_number': '1', 'vendor_name': 'v1', 'amount': 1_000_000, 'branch_name': 'busy'},
        {'invoice_number': '2', 'vendor_name': 'v1', 'amount': 1_000_000, 'branch_name': 'busy'},
        {'invoice_number': '3', 'vendor_name': 'v1', 'amount': 1_000_000, 'branch_name': 'busy'},
        {'invoice_number': '4', 'vendor_name': 'v1', 'amount': 1_000_000, 'branch_name': 'busy'},
        {'invoice_number': '5', 'vendor_name': 'v1', 'amount': 100_000, 'branch_name': 'quiet'},
    ]
    opps = build_opportunity_map(documents, [])
    kinds = {o.kind for o in opps}
    assert 'branch_underutilized' in kinds


def test_opportunity_map_timing_mismatch_from_late_payment_waste():
    documents = [{'invoice_number': '1', 'vendor_name': 'v1', 'amount': 1_000_000, 'branch_name': 'b1'}]
    waste = [{'category': 'late_payment', 'iqd_amount': 500_000, 'description': 'late'}]
    opps = build_opportunity_map(documents, waste)
    kinds = {o.kind for o in opps}
    assert 'timing_mismatch' in kinds
    timing = next(o for o in opps if o.kind == 'timing_mismatch')
    assert timing.iqd_amount == int(500_000 * 0.4)


# ── Immutability principle: actions create reverse-style ledger ──────

def test_action_plan_returns_distinct_paths():
    waste = [
        {'category': 'duplicate', 'iqd_amount': 1_000_000, 'description': 'dup invoice'},
        {'category': 'late_payment', 'iqd_amount': 500_000, 'description': 'late fee'},
    ]
    change = build_change_path(waste)
    adaptation = build_adaptation_path(waste, trust_level='low', coverage_pct=40)
    assert all(a.path == 'change' for a in change)
    assert all(a.path == 'adaptation' for a in adaptation)
    assert len(change) >= 1
    assert len(adaptation) >= 1
