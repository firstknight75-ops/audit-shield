from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from app.exports.certificates import tamper_proof_certificate

try:
    from weasyprint import HTML
except Exception:  # pragma: no cover
    HTML = None


CORE_OUTPUT_TITLES = {
    'true_picture': 'الصورة الحقيقية',
    'trust_index': 'مؤشر الموثوقية',
    'waste_map': 'خريطة الهدر',
    'risk_map': 'خريطة المخاطر',
    'opportunity_map': 'خريطة الفرص',
    'action_plan': 'خطة العمل',
    'dashboards': 'لوحات القيادة',
    'what_if': 'محاكاة ماذا لو',
}


def export_excel(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.sheet_view.rightToLeft = True
    ws.freeze_panes = 'A2'
    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for cell in ws[1]:
            cell.alignment = Alignment(horizontal='right')
            cell.font = Font(bold=True)
        for row in rows:
            ws.append([row.get(h) for h in headers])
            for c in ws[ws.max_row]:
                c.alignment = Alignment(horizontal='right')
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    ws.append([])
    ws.append(['ledger_hash_at_generation', cert['ledger_hash_at_generation']])
    ws.append(['signature', cert['signature']])
    wb.save(path)
    return path


def export_pdf(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    html = f"""
    <html dir='rtl' lang='ar'>
    <head>
      <meta charset='utf-8'>
      <style>
        body {{ font-family: DejaVu Sans, sans-serif; direction: rtl; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #999; padding: 6px; text-align: right; }}
      </style>
    </head>
    <body>
      <h1>{title}</h1>
      <table>
        <thead><tr>{''.join(f'<th>{k}</th>' for k in (rows[0].keys() if rows else []))}</tr></thead>
        <tbody>{''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in row.values()) + '</tr>' for row in rows)}</tbody>
      </table>
      <p>ledger_hash_at_generation: {cert['ledger_hash_at_generation']}</p>
      <p>signature: {cert['signature']}</p>
    </body></html>
    """
    if HTML:
        HTML(string=html).write_pdf(path)
    else:
        Path(path).with_suffix('.html').write_text(html, encoding='utf-8')
        return str(Path(path).with_suffix('.html'))
    return path


def export_png(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    payload = f"PNG EXPORT 300DPI\n{title}\nrows={len(rows)}\nledger={cert['ledger_hash_at_generation']}\nsignature={cert['signature']}\n"
    Path(path).write_text(payload, encoding='utf-8')
    return path
