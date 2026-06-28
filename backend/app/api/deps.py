from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, set_session_context
from app.models.entities import User
from app.security.tokens import decode_token
from app.services.i18n import tr
from app.services.permissions import get_effective_permissions


async def get_current_user(
    authorization: str = Header(default=''),
    x_tenant_schema: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=tr('auth.unauthorized', 'ar'))
    token = authorization.removeprefix('Bearer ').strip()
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=tr('auth.unauthorized', 'ar')) from exc
    if payload.get('type') != 'access':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=tr('auth.unauthorized', 'ar'))
    user = (await db.execute(select(User).where(User.id == payload.get('sub')))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=tr('auth.unauthorized', 'ar'))
    lang = user.preferred_language.value if hasattr(user.preferred_language, 'value') else str(user.preferred_language)
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=tr('auth.locked', lang))
    if user.last_activity_at and user.last_activity_at < now - timedelta(minutes=15):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=tr('auth.session_expired', lang))

    # Set session context for RLS: role and tenant (company_group_id)
    await set_session_context(
        db,
        role=user.role.value,
        tenant_id=str(user.company_group_id),
        tenant_schema=x_tenant_schema,
    )

    user.last_activity_at = now
    await db.commit()
    await db.refresh(user)
    return user


def require_permission(*codes: str):
    async def dependency(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> User:
        effective = await get_effective_permissions(current_user, db)
        lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
        if not all(code in effective for code in codes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=tr('permissions.denied', lang))
        return current_user

    return dependency
