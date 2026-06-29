"""Layer 4 drill-down — original invoice image.

Per AuditCore principle 5: Truth From Data — Owner gets a 4-layer drill-down
from executive summary to the original invoice image.

This endpoint decrypts the encrypted_blob in-memory only and streams the
original file back to the Owner's browser. The plaintext bytes exist only
inside this response generator — they are NOT written to disk or persisted.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import Document, User
from app.models.enums import UserRole
from app.services.access import require_company_access
from app.services.encryption import decrypt_bytes_to_memory
from app.services.i18n import tr
from app.services.ledger import append_ledger_entry

router = APIRouter(prefix='/owner/dashboard/layer4', tags=['layer4'])


@router.get('/{document_id}/image')
async def get_original_image(
    document_id: str,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_analytics')),
    db: AsyncSession = Depends(get_db),
):
    """Decrypt and stream the original invoice image — in-memory only."""
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)

    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))

    document = (await db.execute(
        select(Document).where(Document.id == document_id, Document.company_id == company_id)
    )).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail=tr('layer4.no_image', lang))

    # Decrypt in-memory only — never persist plaintext bytes
    plaintext = await decrypt_bytes_to_memory(
        tenant_or_company=str(company_id),
        file_id=str(document.id),
        data=bytes(document.encrypted_blob),
    )

    # Ledger the access
    await append_ledger_entry(
        db,
        company_id=company_id,
        actor_user_id=current_user.id,
        action_type='layer4_image_accessed',
        action_payload={'document_id': document_id, 'mime': document.mime_type, 'size': document.file_size},
    )
    await db.commit()

    return StreamingResponse(
        iter([plaintext]),
        media_type=document.mime_type or 'application/octet-stream',
        headers={
            'Content-Disposition': f'inline; filename="{document.original_filename}"',
            'X-AuditCore-Mode': 'in-memory-decrypt',
        },
    )
