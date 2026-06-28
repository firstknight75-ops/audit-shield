from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import AuditLedger, DailyTask, User, UserCompanyAccess
from app.models.enums import UserRole
from app.schemas.ledger import LedgerVerifyResponse
from app.services.access import get_accessible_company_ids, require_company_access
from app.services.i18n import tr
from app.services.ledger import verify_ledger_integrity

router = APIRouter(prefix='/owner', tags=['owner'])


@router.get('/ledger/verify', response_model=LedgerVerifyResponse)
async def verify(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_ledger')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    valid, message, broken = await verify_ledger_integrity(db, company_id, lang)
    return LedgerVerifyResponse(valid=valid, message=message, broken_entry_id=broken)


@router.post('/ledger/tamper/{entry_id}')
async def tamper(
    entry_id: str,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_ledger')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    row = (await db.execute(select(AuditLedger).where(AuditLedger.id == entry_id, AuditLedger.company_id == company_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=tr('owner.ledger_entry_not_found', lang))
    row.action_payload = {**row.action_payload, 'tampered': True}
    await db.commit()
    return {'message': tr('owner.ledger_entry_tampered', lang)}


@router.get('/auditor-efficiency')
async def auditor_efficiency(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_analytics')),
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
