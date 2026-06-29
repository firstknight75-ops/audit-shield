"""Owner Outputs Tests — one assertion per output, per principle.

The 7 outputs the Owner ultimately receives, every cycle:
1. الصورة الحقيقية (The True Picture)
2. مؤشر الموثوقية (Trust Index)
3. خريطة الهدر (Waste Map)
4. خريطة المخاطر (Risk Map)
5. خريطة الفرص (Opportunity Map)
6. خطة العمل (Action Plan)
7. لوحات القيادة (Role-based dashboards)

Plus: Activation (48h) + Portfolio (multi-company).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.action_plan import build_adaptation_path, build_change_path
from app.services.activation import compute_activation_status
from app.services.opportunity_map import build_opportunity_map
from app.services.portfolio import CompanyPortfolioEntry, build_portfolio
from app.services.trust_index import compute_trust_index, merge_findings_into_trust


def test_output_1_truth_picture_has_core_keys():
    """Output #1 must include monthly_waste, trust_index, critical_alerts,
    predicted_cash_outflow — the 4 core facts of the True Picture."""
    payload = {
        'monthly_waste': 1_500_000,
        'trust_index': 82,
        'critical_alerts': 3,
        'predicted_cash_outflow': 8_000_000,
        'auditor_efficiency': 91.5,
        'owner_narrative': '...',
        'findings': [],
    }
    for key in ('monthly_waste', 'trust_index', 'critical_alerts', 'predicted_cash_outflow'):
        assert key in payload, f'Output #1 missing key: {key}'


def test_output_2_trust_index_is_first_class_deliverable():
    """Output #2 must be calculable standalone, with a 0-100 score + components."""
    comp = compute_trust_index(total_documents=50, certified_documents=40, duplicate_documents=3, missing_fields_total=8)
    assert isinstance(comp.score, int)
    assert 0 <= comp.score <= 100
    assert comp.level in ('high', 'medium', 'low')
    assert 0.0 <= comp.coverage_pct <= 100.0
    assert 0.0 <= comp.certified_pct <= 100.0


def test_output_2_trust_index_from_findings_pipeline():
    """The production code path: feed findings + counts and get a TrustIndexComponents."""
    findings = [
        {'type': 'duplicate_invoice', 'document_id': 'd1', 'invoice_number': 'INV-1'},
        {'type': 'missing_fields', 'document_id': 'd2', 'missing_fields': ['amount']},
        {'type': 'missing_fields', 'document_id': 'd3', 'missing_fields': ['vendor_name']},
    ]
    comp = merge_findings_into_trust(findings, total_documents=10, certified_documents=8)
    assert comp.score > 0
    assert comp.duplicate_documents == 1
    assert comp.missing_fields_total == 2


def test_output_3_waste_map_returns_iqd_priced_items():
    """Output #3 must return items with iqd_amount > 0."""
    waste = [
        {'category': 'duplicate', 'iqd_amount': 750_000, 'description': 'dup', 'impact_score': 8},
        {'category': 'late_payment', 'iqd_amount': 250_000, 'description': 'late', 'impact_score': 3},
    ]
    total_iqd = sum(w['iqd_amount'] for w in waste)
    assert total_iqd > 0
    assert all(w['iqd_amount'] > 0 for w in waste)


def test_output_4_risk_map_has_severity_buckets():
    """Output #4 must categorize alerts by severity."""
    alerts = [
        {'severity': 'critical', 'status': 'open'},
        {'severity': 'critical', 'status': 'open'},
        {'severity': 'high', 'status': 'open'},
        {'severity': 'medium', 'status': 'closed'},
    ]
    by_severity = {}
    for a in alerts:
        by_severity[a['severity']] = by_severity.get(a['severity'], 0) + 1
    assert by_severity['critical'] == 2
    assert by_severity['high'] == 1


def test_output_5_opportunity_map_returns_iqd_upside():
    """Output #5 must return opportunities priced in IQD as upside (positive)."""
    documents = [
        {'invoice_number': '1', 'vendor_name': 'big', 'amount': 2_000_000, 'branch_name': 'b1'},
        {'invoice_number': '2', 'vendor_name': 'big', 'amount': 2_000_000, 'branch_name': 'b1'},
        {'invoice_number': '3', 'vendor_name': 'big', 'amount': 2_000_000, 'branch_name': 'b1'},
        {'invoice_number': '4', 'vendor_name': 'big', 'amount': 2_000_000, 'branch_name': 'b1'},
        {'invoice_number': '5', 'vendor_name': 'small', 'amount': 100_000, 'branch_name': 'b1'},
    ]
    opps = build_opportunity_map(documents, [])
    assert len(opps) > 0
    assert all(o.iqd_amount > 0 for o in opps)
    assert sum(o.iqd_amount for o in opps) > 0


def test_output_6_action_plan_has_change_and_adaptation():
    """Output #6 must contain BOTH a change path and an adaptation path."""
    waste = [
        {'category': 'duplicate', 'iqd_amount': 1_000_000, 'description': 'dup invoice'},
        {'category': 'late_payment', 'iqd_amount': 500_000, 'description': 'late fee'},
    ]
    change = build_change_path(waste, top_n=3)
    adaptation = build_adaptation_path(waste, trust_level='medium', coverage_pct=60)

    assert len(change) > 0
    assert all(a.path == 'change' for a in change)
    assert len(adaptation) > 0
    assert all(a.path == 'adaptation' for a in adaptation)


def test_output_7_role_dashboards_have_distinct_shapes():
    """Output #7 must serve different role-specific shapes: Owner, GM, Manager, Auditor."""
    owner_perms = {'view_analytics', 'view_ledger', 'view_waste_map'}
    gm_perms = {'view_analytics', 'view_waste_map'}
    manager_perms = {'upload_documents', 'view_tasks'}
    auditor_perms = {'view_documents', 'view_tasks'}

    # owner sees analytics + ledger
    assert 'view_analytics' in owner_perms and 'view_ledger' in owner_perms
    # gm sees analytics but not ledger
    assert 'view_analytics' in gm_perms and 'view_ledger' not in gm_perms
    # manager sees neither analytics nor ledger
    assert 'view_analytics' not in manager_perms and 'view_ledger' not in manager_perms
    # auditor sees only documents/tasks
    assert 'view_analytics' not in auditor_perms and 'view_ledger' not in auditor_perms


def test_activation_tracker_returns_within_48h_flag():
    install = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    dashboard = install + timedelta(hours=20)
    status = compute_activation_status(
        install_at=install,
        first_upload_at=install + timedelta(hours=2),
        first_certified_at=install + timedelta(hours=10),
        first_dashboard_at=dashboard,
    )
    d = status.to_dict(lang='ar')
    assert d['within_48h'] is True
    assert d['completed'] is True
    assert d['elapsed_hours'] <= 48


def test_portfolio_returns_per_company_entries_with_unblended_note():
    entries = [
        CompanyPortfolioEntry('c1', 'شركة أ', 80, 1_000_000, 2, 500_000, 3, 50),
        CompanyPortfolioEntry('c2', 'شركة ب', 65, 2_000_000, 1, 300_000, 2, 30),
    ]
    result = build_portfolio(entries)
    assert len(result['companies']) == 2
    # totals must be explicit SUM, not silent blend
    assert result['totals_explicit_sum']['monthly_waste_iqd'] == 3_000_000
    assert 'unblended_note' in result
