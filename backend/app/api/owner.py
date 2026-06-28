from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.entities import DailyTask, User
from app.models.enums import UserRole
from app.schemas.ledger import LedgerVerifyResponse
from app.services.ledger import verify_ledger_integrity

router = APIRouter(prefix='/owner', tags=['owner'])


@router.get('/ledger/verify', response_model=LedgerVerifyResponse)
async def verify(current_user: User = Depends(require_permission('view_ledger')), db: AsyncSession = Depends(get_db)):
    valid, message, broken = await verify_ledger_integrity(db, current_user.company_id)
    return LedgerVerifyResponse(valid=valid, message=message, broken_entry_id=broken)


@router.get('/auditor-efficiency')
async def auditor_efficiency(current_user: User = Depends(require_permission('view_analytics')), db: AsyncSession = Depends(get_db)):
    auditors = (await db.execute(select(User).where(User.company_id == current_user.company_id, User.role == UserRole.auditor))).scalars().all()
    result = []
    for auditor in auditors:
        tasks = (await db.execute(select(DailyTask).where(DailyTask.auditor_user_id == auditor.id))).scalars().all()
        total = len(tasks)
        on_time = len([t for t in tasks if t.status == 'done' and t.completed_at and t.completed_at <= t.due_at])
        demerits = sum(t.demerit_points for t in tasks)
        efficiency = ((on_time / total) * 100 if total else 100) - (demerits * 5)
        result.append({'auditor': auditor.full_name, 'efficiency': round(efficiency, 2), 'demerits': demerits})
    return result
