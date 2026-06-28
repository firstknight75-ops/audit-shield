from __future__ import annotations

import pandas as pd


def run_cross_reference(procurement: pd.DataFrame, bank: pd.DataFrame, inventory: pd.DataFrame) -> list[dict]:
    findings: list[dict] = []
    if not procurement.empty and not bank.empty and {'invoice_number', 'amount'}.issubset(procurement.columns) and {'invoice_number', 'outflow_amount'}.issubset(bank.columns):
        merged = procurement.merge(bank, on='invoice_number', how='left')
        for _, row in merged.iterrows():
            p = float(row.get('amount') or 0)
            b = float(row.get('outflow_amount') or 0)
            variance = abs(p - b)
            if p and variance > p * 0.01:
                findings.append({'type': 'procurement_bank_mismatch', 'label_ar': 'تضارب مشتريات/بنك', 'invoice_number': row['invoice_number'], 'variance_amount': variance, 'severity': 'critical'})
    if not procurement.empty and not inventory.empty and {'invoice_number', 'amount'}.issubset(procurement.columns) and {'invoice_number', 'inventory_amount'}.issubset(inventory.columns):
        merged = procurement.merge(inventory, on='invoice_number', how='left')
        for _, row in merged.iterrows():
            p = float(row.get('amount') or 0)
            i = float(row.get('inventory_amount') or 0)
            variance = abs(p - i)
            if p and variance > p * 0.05:
                findings.append({'type': 'procurement_inventory_mismatch', 'label_ar': 'تضارب مشتريات/مخزن', 'invoice_number': row['invoice_number'], 'variance_amount': variance, 'severity': 'critical'})
    return findings
