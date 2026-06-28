from app.ai.cross_reference import run_cross_reference
from app.core.factories import BaileysGateway, WhatsAppCloudGateway
import pandas as pd


def test_same_call_signature_for_gateways():
    assert hasattr(BaileysGateway(), 'send')
    assert hasattr(WhatsAppCloudGateway(), 'send')


def test_cross_reference_detects_inventory_mismatch():
    procurement = pd.DataFrame([{'invoice_number': 'INV-1', 'amount': 10000}])
    bank = pd.DataFrame([{'invoice_number': 'INV-1', 'outflow_amount': 10000}])
    inventory = pd.DataFrame([{'invoice_number': 'INV-1', 'inventory_amount': 9000}])
    findings = run_cross_reference(procurement, bank, inventory)
    assert any(f['type'] == 'procurement_inventory_mismatch' for f in findings)
