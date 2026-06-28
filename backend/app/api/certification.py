from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import DailyTask, Document, OCRExtraction, User
from app.schemas.certification import CertificationField, CertificationNextResponse, CertificationRequest
from app.services.ledger import append_ledger_entry
from app.services.ocr import FIELD_LABELS, confidence_color

router = APIRouter(prefix='/certification', tags=['certification'])


def _to_response(extraction: OCRExtraction, document: Document) -> CertificationNextResponse:
    fields = []
    for key, label in FIELD_LABELS.items():
        conf = int(extraction.confidence_map.get(key, 0))
        fields.append(CertificationField(key=key, label=label, value=extraction.extracted_data.get(key, '' if key != 'items_list' else []), confidence=conf, color=confidence_color(conf), requires_correction=conf < 85))
    return CertificationNextResponse(document_id=str(document.id), filename=document.original_filename, extraction_id=str(extraction.id), fields=fields)


@router.get('/next', response_model=CertificationNextResponse | None)
async def next_certification(current_user: User = Depends(require_permission('view_documents')), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(OCRExtraction, Document).join(Document, Document.id == OCRExtraction.document_id).where(OCRExtraction.status == 'pending', Document.company_id == current_user.company_id).order_by(Document.created_at.asc()))).first()
    if not row:
        return None
    extraction, document = row
    return _to_response(extraction, document)


@router.post('/{extraction_id}/certify')
async def certify_document(extraction_id: str, payload: CertificationRequest, current_user: User = Depends(require_permission('view_documents')), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(OCRExtraction, Document).join(Document, Document.id == OCRExtraction.document_id).where(OCRExtraction.id == extraction_id, Document.company_id == current_user.company_id))).first()
    if not row:
        raise HTTPException(status_code=404, detail='المستند غير موجود.')
    extraction, document = row
    for key, conf in extraction.confidence_map.items():
        if conf < 85:
            incoming = payload.fields.get(key)
            if incoming in (None, '', []):
                raise HTTPException(status_code=400, detail=f'يجب تصحيح الحقل {FIELD_LABELS.get(key, key)} قبل الاعتماد.')
    extraction.extracted_data = payload.fields
    extraction.status = 'certified'
    extraction.certified_at = datetime.now(timezone.utc)
    extraction.certified_by_user_id = current_user.id
    await append_ledger_entry(db, current_user.company_id, current_user.id, 'document_certified', {'extraction_id': extraction_id, 'document_id': str(extraction.document_id), 'fields': payload.fields})
    task = (await db.execute(select(DailyTask).where(DailyTask.source_document_id == extraction.document_id, DailyTask.status == 'open'))).scalars().first()
    if task:
        task.status = 'done'
        task.completed_at = datetime.now(timezone.utc)
        await append_ledger_entry(db, current_user.company_id, current_user.id, 'task_status_changed', {'task_id': str(task.id), 'status': 'done'})
    await db.commit()
    next_row = (await db.execute(select(OCRExtraction, Document).join(Document, Document.id == OCRExtraction.document_id).where(OCRExtraction.status == 'pending', Document.company_id == current_user.company_id).order_by(Document.created_at.asc()))).first()
    return {'message': 'تم اعتماد المستند بنجاح.', 'next': _to_response(*next_row) if next_row else None}
