from __future__ import annotations

import pandas as pd


def run_anomaly_detection(df: pd.DataFrame) -> list[dict]:
    findings: list[dict] = []
    if df.empty or len(df) < 30 or 'amount' not in df.columns:
        return findings
    amounts = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    mean = amounts.mean()
    std = amounts.std(ddof=0)
    if std > 0:
        zscores = (amounts - mean) / std
        for idx, z in zscores.items():
            if abs(z) > 3:
                row = df.loc[idx]
                findings.append({'type': 'zscore_outlier', 'label_ar': 'قيمة شاذة', 'document_id': str(row.get('document_id', '')), 'amount': float(row.get('amount', 0)), 'z_score': float(z), 'severity': 'high'})
    q1 = amounts.quantile(0.25)
    q3 = amounts.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    for idx, val in amounts.items():
        if val < lower or val > upper:
            row = df.loc[idx]
            findings.append({'type': 'iqr_outlier', 'label_ar': 'خارج النطاق المعتاد', 'document_id': str(row.get('document_id', '')), 'amount': float(val), 'severity': 'high'})
    if 'serial' in df.columns:
        serials = sorted(pd.to_numeric(df['serial'], errors='coerce').dropna().astype(int).unique().tolist())
        for i in range(1, len(serials)):
            if serials[i] - serials[i - 1] > 1:
                findings.append({'type': 'serial_gap', 'label_ar': 'فجوة تسلسلية', 'from': serials[i - 1], 'to': serials[i], 'severity': 'normal'})
    return findings
