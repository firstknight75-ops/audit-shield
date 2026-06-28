from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import LoginRequest, MeResponse, RefreshRequest, TokenResponse
from app.security.passwords import verify_password
from app.security.tokens import create_token, decode_token
from app.services.permissions import get_effective_permissions

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='بيانات الدخول غير صحيحة.')
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail='تم قفل الحساب لمدة 15 دقيقة.')
    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            user.failed_login_attempts = 0
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='بيانات الدخول غير صحيحة.')
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_activity_at = now
    await db.commit()
    return TokenResponse(access_token=create_token(str(user.id), 'access', 15), refresh_token=create_token(str(user.id), 'refresh', 1440))


@router.post('/refresh', response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        claims = decode_token(payload.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='رمز التحديث غير صالح.') from exc
    if claims.get('type') != 'refresh':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='رمز التحديث غير صالح.')
    user = (await db.execute(select(User).where(User.id == claims.get('sub')))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='المستخدم غير متاح.')
    user.last_activity_at = datetime.now(timezone.utc)
    await db.commit()
    return TokenResponse(access_token=create_token(str(user.id), 'access', 15), refresh_token=create_token(str(user.id), 'refresh', 1440))


@router.get('/me', response_model=MeResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> MeResponse:
    permissions = await get_effective_permissions(current_user, db)
    return MeResponse(id=str(current_user.id), email=current_user.email, full_name=current_user.full_name, role=current_user.role.value, permissions=permissions, last_activity_at=current_user.last_activity_at)
