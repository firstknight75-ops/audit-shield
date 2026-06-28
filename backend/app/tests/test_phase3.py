from app.ai.cross_reference import run_cross_reference
from app.ai.data_quality import run_data_quality
from app.ai.impact import findings_to_waste_items
import pandas as pd


def test_duplicate_invoice_and_inventory_mismatch_flagged():
    procurement = pd.DataFrame([
        {'document_id': '1', 'invoice_number': 'INV-1', 'amount': 1000},
        {'document_id': '2', 'invoice_number': 'INV-1', 'amount': 1000},
        {'document_id': '3', 'invoice_number': 'INV-2', 'amount': 2000},
    ])
    bank = pd.DataFrame([
        {'invoice_number': 'INV-1', 'outflow_amount': 1000},
        {'invoice_number': 'INV-2', 'outflow_amount': 2000},
    ])
    inventory = pd.DataFrame([
        {'invoice_number': 'INV-1', 'inventory_amount': 1000},
        {'invoice_number': 'INV-2', 'inventory_amount': 1500},
    ])
    quality = run_data_quality(procurement)
    cross = run_cross_reference(procurement, bank, inventory)
    findings = quality + cross
    labels = [f['type'] for f in findings]
    assert 'duplicate_invoice' in labels
    assert 'procurement_inventory_mismatch' in labels
    waste = findings_to_waste_items(findings)
    assert len(waste) >= 2
