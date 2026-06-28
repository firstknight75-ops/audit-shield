from __future__ import annotations

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment

from app.exports.certificates import tamper_proof_certificate


def export_excel(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.sheet_view.rightToLeft = True
    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for cell in ws[1]:
            cell.alignment = Alignment(horizontal='right')
        for row in rows:
            ws.append([row.get(h) for h in headers])
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    ws.append([])
    ws.append(['ledger_hash_at_generation', cert['ledger_hash_at_generation']])
    ws.append(['signature', cert['signature']])
    wb.save(path)
    return path


def export_pdf(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    html = f"<html dir='rtl'><body><h1>{title}</h1><p>عدد الصفوف: {len(rows)}</p><p>ledger_hash_at_generation: {cert['ledger_hash_at_generation']}</p><p>signature: {cert['signature']}</p></body></html>"
    Path(path).write_text(html, encoding='utf-8')
    return path


def export_png(path: str, title: str, rows: list[dict], ledger_hash: str) -> str:
    cert = tamper_proof_certificate({'title': title, 'rows_count': len(rows)}, ledger_hash)
    png_stub = f"PNG EXPORT\n{title}\nrows={len(rows)}\nledger={cert['ledger_hash_at_generation']}\nsignature={cert['signature']}\n"
    Path(path).write_text(png_stub, encoding='utf-8')
    return path
