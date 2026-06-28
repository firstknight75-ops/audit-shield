from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.entities import AuditLedger, Branch, Permission, User, UserPermissionOverride
from app.models.enums import OverrideAction, UserRole
from app.schemas.admin import PermissionOverrideRequest, UserCreateRequest
from app.security.passwords import get_password_hash
from app.services.ledger import append_ledger_entry

router = APIRouter(prefix='/admin', tags=['admin'])


@router.post('/users')
async def create_user(payload: UserCreateRequest, current_user: User = Depends(require_permission('manage_users')), db: AsyncSession = Depends(get_db)):
    user = User(email=payload.email, hashed_password=get_password_hash(payload.password), full_name=payload.full_name, role=UserRole(payload.role), branch_id=payload.branch_id, company_id=current_user.company_id, is_active=True)
    db.add(user)
    await append_ledger_entry(db, current_user.company_id, current_user.id, 'user_created', {'email': payload.email})
    await db.commit()
    return {'message': 'تم إنشاء المستخدم بنجاح.'}


@router.post('/users/{user_id}/deactivate')
async def deactivate_user(user_id: str, current_user: User = Depends(require_permission('manage_users')), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id, User.company_id == current_user.company_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='المستخدم غير موجود.')
    user.is_active = False
    await append_ledger_entry(db, current_user.company_id, current_user.id, 'user_deactivated', {'user_id': user_id})
    await db.commit()
    return {'message': 'تم تعطيل المستخدم.'}


@router.post('/permissions/override')
async def set_override(payload: PermissionOverrideRequest, current_user: User = Depends(require_permission('manage_permissions')), db: AsyncSession = Depends(get_db)):
    permission = (await db.execute(select(Permission).where(Permission.code == payload.permission_code))).scalar_one_or_none()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='الصلاحية غير موجودة.')
    if permission.category == 'app_owner':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='لا يمكن منح صلاحيات مالك المنصة من هذه اللوحة.')
    override = UserPermissionOverride(user_id=payload.user_id, permission_id=permission.id, action=OverrideAction(payload.action), reason=payload.reason, expires_at=payload.expires_at, created_by_user_id=current_user.id, is_active=True)
    db.add(override)
    await append_ledger_entry(db, current_user.company_id, current_user.id, 'permission_override', {'user_id': payload.user_id, 'permission_code': payload.permission_code, 'action': payload.action, 'expires_at': payload.expires_at.isoformat() if payload.expires_at else None})
    await db.commit()
    return {'message': 'تم تحديث الصلاحية بنجاح.'}


@router.get('/activity')
async def activity_feed(current_user: User = Depends(require_permission('view_ledger')), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(AuditLedger).where(AuditLedger.company_id == current_user.company_id).order_by(AuditLedger.created_at.desc()))).scalars().all()


@router.get('/branches')
async def branches(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Branch).where(Branch.company_id == current_user.company_id))).scalars().all()
