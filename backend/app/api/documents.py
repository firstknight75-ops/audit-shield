from __future__ import annotations

import os
import uuid

import magic
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import Document, OCRExtraction, User
from app.schemas.document import DocumentUploadResponse
from app.services.access import require_company_access
from app.services.encryption import encrypt_bytes, validate_encrypted_json_structure
from app.services.i18n import tr
from app.services.ledger import append_ledger_entry
from app.workers.tasks import process_ocr_document

router = APIRouter(prefix='/documents', tags=['documents'])

ALLOWED_EXTENSIONS = {'.xlsx', '.csv', '.docx', '.jpg', '.png', '.tiff', '.pdf', '.json'}
ALLOWED_MIME = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'application/pdf',
    'application/json',
}


@router.post('/upload', response_model=DocumentUploadResponse)
async def upload_document(
    company_id: str = Form(...),
    branch_id: str | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission('upload_documents')),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tr('documents.company_required', lang))
    if not await require_company_access(current_user, db, company_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=tr('permissions.denied', lang))
    extension = os.path.splitext(file.filename or '')[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tr('documents.invalid_extension', lang))
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tr('documents.too_large', lang))
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tr('documents.invalid_type', lang))
    if extension == '.pdf' and mime_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tr('documents.invalid_type', lang))
    if extension == '.json' and not await validate_encrypted_json_structure(content):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=tr('documents.invalid_json', lang))
    file_id = str(uuid.uuid4())
    encrypted = await encrypt_bytes(str(current_user.company_group_id), file_id, content)
    document = Document(id=file_id, company_id=company_id, branch_id=branch_id, uploaded_by_user_id=current_user.id, original_filename=file.filename or file_id, mime_type=mime_type, file_size=len(content), encrypted_blob=encrypted, metadata_json={'encrypted': True, 'ocr_status': 'queued'})
    extraction = OCRExtraction(document_id=file_id, status='queued', extracted_data={}, confidence_map={}, raw_text=None, page_count=1)
    db.add(document)
    db.add(extraction)
    await append_ledger_entry(db, company_id, current_user.id, 'document_uploaded', {'document_id': file_id, 'filename': document.original_filename, 'company_id': company_id, 'branch_id': branch_id})
    await db.commit()
    process_ocr_document.delay(file_id)
    return DocumentUploadResponse(id=file_id, filename=document.original_filename, mime_type=mime_type, size=len(content))
