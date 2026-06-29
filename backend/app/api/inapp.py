"""In-app notification inbox API.

GET /api/inapp/unread — count
GET /api/inapp/recent — last 50
POST /api/inapp/{id}/read — mark as read
POST /api/inapp/read-all — mark all as read
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import InAppNotification, User

router = APIRouter(prefix='/inapp', tags=['inapp'])


@router.get('/unread')
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    count = (await db.execute(
        select(func.count(InAppNotification.id))
        .where(InAppNotification.user_id == current_user.id, InAppNotification.read_at.is_(None))
    )).scalar()
    return {'count': count or 0}


@router.get('/recent')
async def recent(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(InAppNotification)
        .where(InAppNotification.user_id == current_user.id)
        .order_by(InAppNotification.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )).scalars().all()
    return [
        {
            'id': str(r.id),
            'title': r.title,
            'body': r.body,
            'severity': r.severity,
            'link': r.link,
            'read_at': r.read_at.isoformat() if r.read_at else None,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post('/{notif_id}/read')
async def mark_read(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notif = (await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notif_id,
            InAppNotification.user_id == current_user.id,
        )
    )).scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail='not_found')
    notif.read_at = datetime_if_now()  # set to now
    await db.commit()
    return {'ok': True}


@router.post('/read-all')
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(InAppNotification)
        .where(InAppNotification.user_id == current_user.id, InAppNotification.read_at.is_(None))
        .values(read_at=datetime_if_now())
    )
    await db.commit()
    return {'ok': True}


def datetime_if_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
