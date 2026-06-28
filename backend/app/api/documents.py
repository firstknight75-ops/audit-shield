from __future__ import annotations

import os
import uuid

import magic
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import Document, User
from app.schemas.document import DocumentUploadResponse
from app.services.encryption import encrypt_bytes, validate_encrypted_json_structure

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
async def upload_document(file: UploadFile = File(...), current_user: User = Depends(require_permission('upload_documents')), db: AsyncSession = Depends(get_db)) -> DocumentUploadResponse:
    extension = os.path.splitext(file.filename or '')[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='امتداد الملف غير مسموح.')
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='حجم الملف يتجاوز 50 ميغابايت.')
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='نوع الملف غير صالح.')
    if extension == '.pdf' and mime_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='امتداد الملف لا يطابق نوعه الحقيقي.')
    if extension == '.json' and not await validate_encrypted_json_structure(content):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='بنية JSON غير صالحة.')
    file_id = str(uuid.uuid4())
    encrypted = await encrypt_bytes(str(current_user.company_id), file_id, content)
    document = Document(id=file_id, company_id=current_user.company_id, branch_id=current_user.branch_id, uploaded_by_user_id=current_user.id, original_filename=file.filename or file_id, mime_type=mime_type, file_size=len(content), encrypted_blob=encrypted, metadata_json={'encrypted': True})
    db.add(document)
    await db.commit()
    return DocumentUploadResponse(id=file_id, filename=document.original_filename, mime_type=mime_type, size=len(content))
