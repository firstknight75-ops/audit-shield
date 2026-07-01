"""Activation + overdue-install endpoints (Phase 4).

Per Phase 4 spec:
- 48-hour activation tracker visible to Owner
- App Owner Clients tab lists every group, with overdue installs flagged
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Company, User
from app.models.enums import UserRole
from app.services.access import require_company_access
from app.services.activation_tracker import compute_activation_progress, flag_overdue_installs
from app.services.i18n import tr

router = APIRouter(tags=['activation'])


@router.get('/owner/activation-progress')
async def owner_activation_progress(
    company_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Owner-facing 48-hour activation tracker for the company they manage."""
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail='company_not_found')
    progress = await compute_activation_progress(db, str(company.company_group_id), lang=lang)
    return progress.to_dict(lang=lang)


@router.get('/appowner/overdue-installs')
async def appowner_overdue_installs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """App Owner-only — returns IDs of installs that missed the 48h SLA."""
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    flagged = await flag_overdue_installs(db)
    return {
        'count': len(flagged),
        'group_ids': flagged,
        'message': tr('appowner.ops_event_registered', lang),
    }
