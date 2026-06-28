from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from app.exports.certificates import tamper_proof_certificate

try:
    from weasyprint import HTML
except Exception:  # pragma: no cover
    HTML = None

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


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
    headers = list(rows[0].keys()) if rows else []
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
        <thead><tr>{''.join(f'<th>{k}</th>' for k in headers)}</tr></thead>
        <tbody>{''.join('<tr>' + ''.join(f'<td>{row.get(h, "")}</td>' for h in headers) + '</tr>' for row in rows)}</tbody>
      </table>
      <p>ledger_hash_at_generation: {cert['ledger_hash_at_generation']}</p>
      <p>signature: {cert['signature']}</p>
    </body></html>
    """
    if HTML:
        HTML(string=html).write_pdf(path)
        return path
    html_path = str(Path(path).with_suffix('.html'))
    Path(html_path).write_text(html, encoding='utf-8')
    return html_path


def export_png(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    if Image and ImageDraw:
        img = Image.new('RGB', (1600, 1200), 'white')
        draw = ImageDraw.Draw(img)
        draw.text((40, 40), f'{title} (300 DPI)', fill='black')
        y = 120
        for row in rows[:15]:
            draw.text((40, y), str(row), fill='black')
            y += 50
        draw.text((40, 1080), f"ledger={cert['ledger_hash_at_generation']}", fill='black')
        draw.text((40, 1130), f"sig={cert['signature'][:32]}", fill='black')
        img.save(path, dpi=(300, 300))
        return path
    fallback = Path(path).with_suffix('.txt')
    payload = (
        f"PNG EXPORT 300DPI\n"
        f"{title}\n"
        f"rows={len(rows)}\n"
        f"ledger={cert['ledger_hash_at_generation']}\n"
        f"signature={cert['signature']}\n"
    )
    fallback.write_text(payload, encoding='utf-8')
    return str(fallback)
