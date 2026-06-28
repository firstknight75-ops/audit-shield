from __future__ import annotations


def findings_to_waste_items(findings: list[dict]) -> list[dict]:
    items: list[dict] = []
    for finding in findings:
        amount = float(finding.get('variance_amount') or finding.get('amount') or 0)
        if amount <= 0 and finding.get('type') == 'duplicate_invoice':
            amount = 0
        items.append({
            'category': finding.get('type', 'finding'),
            'description': finding.get('label_ar', 'مؤشر تحليلي'),
            'impact_score': int(min(max(amount / 1000000, 1), 10)) if amount else 1,
            'iqd_amount': amount,
            'severity': finding.get('severity', 'normal'),
            'invoice_number': finding.get('invoice_number'),
        })
    return items
