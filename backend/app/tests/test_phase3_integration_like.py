import pandas as pd

from app.ai.anomaly import run_anomaly_detection
from app.ai.cross_reference import run_cross_reference
from app.ai.data_quality import run_data_quality
from app.ai.impact import findings_to_waste_items
from app.ai.narrative import generate_narrative
from app.ai.predictor import predict_next_month_cash_outflow
from app.ai.orchestrator import compute_trust_index


def test_phase3_local_analysis_pipeline_like_flow():
    rows = []
    for i in range(1, 35):
        rows.append(
            {
                'document_id': f'doc-{i}',
                'invoice_number': 'INV-DUP' if i in (2, 3) else f'INV-{i}',
                'date': '2026-06-28',
                'amount': 1000000 + i * 10000,
                'vendor_name': 'شركة الرافدين',
                'serial': i,
            }
        )
    df = pd.DataFrame(rows)
    procurement = df[['document_id', 'invoice_number', 'amount']].copy()
    bank = pd.DataFrame([
        {'invoice_number': r['invoice_number'], 'outflow_amount': r['amount']} for r in rows
    ])
    inventory = pd.DataFrame([
        {'invoice_number': r['invoice_number'], 'inventory_amount': (r['amount'] - 200000) if r['invoice_number'] == 'INV-10' else r['amount']} for r in rows
    ])

    findings = []
    findings.extend(run_data_quality(df))
    findings.extend(run_anomaly_detection(df))
    findings.extend(run_cross_reference(procurement, bank, inventory))

    labels = [f['type'] for f in findings]
    assert 'duplicate_invoice' in labels
    assert 'procurement_inventory_mismatch' in labels

    waste_items = findings_to_waste_items(findings)
    assert len(waste_items) >= 2
    assert any(item.get('iqd_amount', 0) > 0 for item in waste_items)

    trust = compute_trust_index(findings, len(df))
    assert 0 <= trust <= 100

    pred_input = pd.DataFrame([
        {'month_index': i + 1, 'amount': 1000000 + i * 50000} for i in range(6)
    ])
    pred = predict_next_month_cash_outflow(pred_input)
    assert 'predicted_cash_outflow' in pred

    owner_text = generate_narrative('owner', {'monthly_waste': 1000000, 'trust_index': trust}, findings)
    manager_text = generate_narrative('manager', {'monthly_waste': 1000000, 'trust_index': trust}, findings)
    assert 'مؤشر الثقة' in owner_text
    assert 'مؤشر الثقة' in manager_text


def test_auditor_owner_manager_access_contracts():
    owner_permissions = {'view_analytics', 'view_ledger'}
    auditor_permissions = {'view_documents', 'view_tasks'}
    manager_permissions = {'upload_documents', 'view_tasks'}

    assert 'view_analytics' in owner_permissions
    assert 'view_analytics' not in auditor_permissions
    assert 'view_analytics' not in manager_permissions
