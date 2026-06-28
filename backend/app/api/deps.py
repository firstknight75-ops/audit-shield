from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, set_session_context
from app.models.entities import User
from app.security.tokens import decode_token
from app.services.permissions import get_effective_permissions


async def get_current_user(authorization: str = Header(default=''), x_tenant_schema: str | None = Header(default=None), db: AsyncSession = Depends(get_db)) -> User:
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='غير مصرح لك بالوصول.')
    token = authorization.removeprefix('Bearer ').strip()
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='غير مصرح لك بالوصول.') from exc
    if payload.get('type') != 'access':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='غير مصرح لك بالوصول.')
    user = (await db.execute(select(User).where(User.id == payload.get('sub')))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='غير مصرح لك بالوصول.')
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail='تم قفل الحساب مؤقتًا بسبب محاولات تسجيل دخول فاشلة.')
    if user.last_activity_at and user.last_activity_at < now - timedelta(minutes=15):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='انتهت الجلسة بسبب عدم النشاط.')
    await set_session_context(db, role=user.role.value, tenant_schema=x_tenant_schema)
    user.last_activity_at = now
    await db.commit()
    await db.refresh(user)
    return user


def require_permission(*codes: str):
    async def dependency(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> User:
        effective = await get_effective_permissions(current_user, db)
        if not all(code in effective for code in codes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='ليس لديك الصلاحية المطلوبة.')
        return current_user

    return dependency
