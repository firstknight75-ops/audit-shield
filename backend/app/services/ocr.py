from __future__ import annotations

import io
import re
import time

from PIL import Image

try:
    import pytesseract
    from pdf2image import convert_from_bytes
except Exception:  # pragma: no cover
    pytesseract = None
    convert_from_bytes = None

FIELD_LABELS = {
    'invoice_number': 'رقم الفاتورة',
    'date': 'التاريخ',
    'amount': 'المبلغ',
    'vendor_name': 'اسم المورد',
    'items_list': 'قائمة الأصناف',
}


def confidence_color(conf: int) -> str:
    if conf >= 85:
        return 'green'
    if conf >= 60:
        return 'yellow'
    return 'red'


def _extract_fields(text: str) -> tuple[dict, dict]:
    invoice = re.search(r'(INV[-\s]?\d{4}[-\s]?\d+|رقم الفاتورة[:\s]*([A-Z0-9\-/]+))', text, re.I)
    date = re.search(r'(20\d{2}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]20\d{2})', text)
    amount = re.search(r'([\d,]+\.?\d*)\s*(?:د\.ع|IQD)?', text)
    vendor = re.search(r'(شركة[^\n]+|المورد[:\s]*[^\n]+)', text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    items = [ln for ln in lines if any(ch.isdigit() for ch in ln)][1:4]
    data = {
        'invoice_number': invoice.group(1) if invoice else '',
        'date': date.group(1) if date else '',
        'amount': amount.group(1) if amount else '',
        'vendor_name': vendor.group(1) if vendor else '',
        'items_list': items or [],
    }
    conf = {}
    for k, v in data.items():
        if v in ('', []):
            conf[k] = 0
        elif k in {'invoice_number', 'date'}:
            conf[k] = 90
        elif k == 'vendor_name':
            conf[k] = 82
        elif k == 'amount':
            conf[k] = 58 if ',' in str(v) else 76
        else:
            conf[k] = 80
    return data, conf


def parse_document_bytes(content: bytes, mime_type: str) -> tuple[str, int, int]:
    started = time.time()
    text = ''
    pages = 1
    if mime_type == 'application/pdf' and convert_from_bytes:
        images = convert_from_bytes(content)
        pages = len(images)
        for image in images:
            if pytesseract:
                text += '\n' + pytesseract.image_to_string(image, lang='ara')
    elif mime_type.startswith('image/'):
        image = Image.open(io.BytesIO(content))
        if pytesseract:
            text = pytesseract.image_to_string(image, lang='ara')
    else:
        try:
            text = content.decode('utf-8', errors='ignore')
        except Exception:
            text = ''
    elapsed = int((time.time() - started) * 1000)
    return text, max(pages, 1), elapsed


def build_extraction_payload(text: str) -> tuple[dict, dict]:
    return _extract_fields(text)
