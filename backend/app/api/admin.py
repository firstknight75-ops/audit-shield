from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.entities import AuditLedger, Branch, Company, Permission, User, UserCompanyAccess, UserPermissionOverride
from app.models.enums import OverrideAction, PreferredLanguage, UserRole
from app.schemas.admin import CompanyAccessGrant, PermissionOverrideRequest, UpdateLanguageRequest, UserCreateRequest
from app.security.passwords import get_password_hash
from app.services.access import get_accessible_company_ids, require_company_access
from app.services.i18n import tr
from app.services.ledger import append_ledger_entry

router = APIRouter(prefix='/admin', tags=['admin'])


@router.post('/users')
async def create_user(
    payload: UserCreateRequest,
    current_user: User = Depends(require_permission('manage_company_users')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)

    # New users belong to the same company_group as the creator
    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole(payload.role),
        company_group_id=current_user.company_group_id,
        is_active=True,
        preferred_language=PreferredLanguage(payload.preferred_language) if payload.preferred_language else PreferredLanguage.ar,
        last_activity_at=None,
    )
    db.add(new_user)
    await db.flush()

    # Grant company access rows
    for grant in payload.company_access:
        if not await require_company_access(current_user, db, grant.company_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=tr('permissions.denied', lang))
        access = UserCompanyAccess(
            user_id=new_user.id,
            company_id=grant.company_id,
            branch_id=grant.branch_id,
            granted_by=current_user.id,
        )
        db.add(access)

    await append_ledger_entry(db, payload.company_access[0].company_id if payload.company_access else None, current_user.id, 'user_created', {'email': payload.email, 'role': payload.role})
    await db.commit()
    return {'message': tr('admin.user_created', lang)}


@router.post('/users/{user_id}/deactivate')
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_permission('manage_company_users')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    accessible_ids = await get_accessible_company_ids(current_user, db)
    user = (await db.execute(select(User).where(User.id == user_id, User.company_group_id == current_user.company_group_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=tr('admin.user_not_found', lang))
    user.is_active = False
    # Find any shared company for ledger
    shared_company = accessible_ids[0] if accessible_ids else None
    await append_ledger_entry(db, shared_company, current_user.id, 'user_deactivated', {'user_id': user_id})
    await db.commit()
    return {'message': tr('admin.user_deactivated', lang)}


@router.post('/permissions/override')
async def set_override(
    payload: PermissionOverrideRequest,
    current_user: User = Depends(require_permission('manage_permissions')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    permission = (await db.execute(select(Permission).where(Permission.code == payload.permission_code))).scalar_one_or_none()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=tr('admin.permission_not_found', lang))
    if permission.category == 'app_owner':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=tr('admin.cannot_override_appowner', lang))

    # If company_id is specified, verify current user has access to that company
    if payload.company_id:
        if not await require_company_access(current_user, db, payload.company_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=tr('permissions.denied', lang))

    override = UserPermissionOverride(
        user_id=payload.user_id,
        permission_id=permission.id,
        company_id=payload.company_id,
        action=OverrideAction(payload.action),
        reason=payload.reason,
        expires_at=payload.expires_at,
        created_by_user_id=current_user.id,
        is_active=True,
    )
    db.add(override)

    ledger_company = payload.company_id or (await get_accessible_company_ids(current_user, db))[0] if (await get_accessible_company_ids(current_user, db)) else None
    await append_ledger_entry(db, ledger_company, current_user.id, 'permission_override', {'user_id': payload.user_id, 'permission_code': payload.permission_code, 'action': payload.action, 'company_id': payload.company_id})
    await db.commit()
    return {'message': tr('admin.permission_updated', lang)}


@router.get('/activity')
async def activity_feed(
    current_user: User = Depends(require_permission('view_audit_ledger')),
    db: AsyncSession = Depends(get_db),
):
    accessible_ids = await get_accessible_company_ids(current_user, db)
    if not accessible_ids:
        return []
    rows = (await db.execute(
        select(AuditLedger)
        .where(AuditLedger.company_id.in_(accessible_ids))
        .order_by(AuditLedger.created_at.desc())
    )).scalars().all()
    return rows


@router.get('/branches')
async def branches(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=tr('permissions.denied', lang))
    return (await db.execute(select(Branch).where(Branch.company_id == company_id))).scalars().all()


@router.get('/companies')
async def list_companies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accessible_ids = await get_accessible_company_ids(current_user, db)
    companies = (await db.execute(select(Company).where(Company.id.in_(accessible_ids)))).scalars().all()
    return [{'id': str(c.id), 'name': c.name, 'sector': c.sector} for c in companies]


@router.post('/language')
async def update_language(
    payload: UpdateLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persist preferred_language change to user record."""
    try:
        lang_enum = PreferredLanguage(payload.preferred_language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f'Unsupported language: {payload.preferred_language}')
    current_user.preferred_language = lang_enum
    await db.commit()
    return {'preferred_language': current_user.preferred_language.value}
