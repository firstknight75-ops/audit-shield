from __future__ import annotations

import pandas as pd


def run_data_quality(df: pd.DataFrame) -> list[dict]:
    findings: list[dict] = []
    if df.empty:
        return findings
    if 'invoice_number' in df.columns:
        duplicates = df[df.duplicated(subset=['invoice_number'], keep=False)]
        for _, row in duplicates.iterrows():
            findings.append({
                'type': 'duplicate_invoice',
                'label_ar': 'فاتورة مكررة',
                'invoice_number': row.get('invoice_number'),
                'document_id': str(row.get('document_id', '')),
                'severity': 'critical',
            })
    missing_cols = [c for c in ['invoice_number', 'date', 'amount', 'vendor_name'] if c in df.columns]
    for _, row in df.iterrows():
        missing = [c for c in missing_cols if pd.isna(row.get(c)) or str(row.get(c)).strip() == '']
        if missing:
            findings.append({
                'type': 'missing_fields',
                'label_ar': 'حقول مفقودة',
                'document_id': str(row.get('document_id', '')),
                'missing_fields': missing,
                'severity': 'high',
            })
    return findings
