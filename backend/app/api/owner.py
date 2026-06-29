from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import AuditLedger, DailyTask, User, UserCompanyAccess
from app.models.enums import UserRole
from app.schemas.ledger import LedgerVerifyResponse
from app.services.access import get_accessible_company_ids, require_company_access
from app.services.i18n import tr
from app.services.ledger import append_reverse_entry, verify_ledger_integrity

router = APIRouter(prefix='/owner', tags=['owner'])


@router.get('/ledger/verify', response_model=LedgerVerifyResponse)
async def verify(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_audit_ledger')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    valid, message, broken = await verify_ledger_integrity(db, company_id, lang)
    return LedgerVerifyResponse(valid=valid, message=message, broken_entry_id=broken)


class ReverseEntryRequest(BaseModel):
    reason: str
    correction: dict | None = None


@router.post('/ledger/reverse/{entry_id}')
async def reverse_entry(
    entry_id: str,
    payload: ReverseEntryRequest,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_audit_ledger')),
    db: AsyncSession = Depends(get_db),
):
    """Production mechanism for corrections — appends a reverse entry.

    Per Phase 2 spec, nothing in audit_ledger is ever updated or deleted.
    Corrections are reverse entries, documented, and permanently visible
    next to the original.
    """
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail=tr('ledger.reverse_reason_required', lang))
    try:
        entry = await append_reverse_entry(
            db,
            company_id=company_id,
            actor_user_id=current_user.id,
            target_entry_id=entry_id,
            reason=payload.reason.strip(),
            correction_payload=payload.correction,
        )
        await db.commit()
        return {
            'message': tr('ledger.reverse_created', lang),
            'reverse_entry_id': str(entry.id),
            'target_entry_id': entry_id,
            'reason': payload.reason.strip(),
            'created_at': entry.created_at.isoformat() if entry.created_at else None,
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=tr('ledger.reverse_target_not_found', lang))


@router.post('/ledger/tamper/{entry_id}')
async def tamper(
    entry_id: str,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_audit_ledger')),
    db: AsyncSession = Depends(get_db),
):
    """TEST-ONLY: simulates a direct mutation to demonstrate tamper detection.

    In production, all corrections go through `/owner/ledger/reverse/{entry_id}`.
    This endpoint exists ONLY so the Owner can verify the chain still
    detects direct mutations — proving the integrity guarantee holds.
    """
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    row = (await db.execute(select(AuditLedger).where(AuditLedger.id == entry_id, AuditLedger.company_id == company_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=tr('owner.ledger_entry_not_found', lang))
    # Mutate the row to simulate a tampering attempt (e.g. compromised admin,
    # direct DB access). verify_ledger_integrity will detect this on next call.
    row.action_payload = {**row.action_payload, 'tampered': True}
    await db.commit()
    return {
        'message': tr('owner.ledger_entry_tampered', lang),
        'note': tr('ledger.tamper_test_only', lang),
    }


@router.get('/auditor-efficiency')
async def auditor_efficiency(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))

    # Find auditors with access to this company
    access_rows = (await db.execute(
        select(UserCompanyAccess.user_id)
        .where(UserCompanyAccess.company_id == company_id)
    )).scalars().all()
    auditors = (await db.execute(
        select(User).where(User.id.in_(access_rows), User.role == UserRole.auditor)
    )).scalars().all()

    result = []
    for auditor in auditors:
        tasks = (await db.execute(select(DailyTask).where(DailyTask.auditor_user_id == auditor.id, DailyTask.company_id == company_id))).scalars().all()
        total = len(tasks)
        on_time = len([t for t in tasks if t.status == 'done' and t.completed_at and t.completed_at <= t.due_at])
        demerits = sum(t.demerit_points for t in tasks)
        efficiency = ((on_time / total) * 100 if total else 100) - (demerits * 5)
        result.append({'auditor': auditor.full_name, 'efficiency': round(efficiency, 2), 'demerits': demerits})
    return result
