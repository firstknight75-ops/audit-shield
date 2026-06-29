from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Permission, RolePermission, User, UserPermissionOverride


async def get_effective_permissions(user: User, session: AsyncSession) -> list[str]:
    role_stmt = select(Permission.code).join(RolePermission, RolePermission.permission_id == Permission.id).where(RolePermission.role == user.role)
    role_codes = set((await session.execute(role_stmt)).scalars().all())
    now = datetime.now(timezone.utc)
    overrides_stmt = select(Permission.code, UserPermissionOverride.action).join(
        UserPermissionOverride, UserPermissionOverride.permission_id == Permission.id
    ).where(
        UserPermissionOverride.user_id == user.id,
        UserPermissionOverride.is_active.is_(True),
        (UserPermissionOverride.expires_at.is_(None) | (UserPermissionOverride.expires_at > now)),
    )
    rows = (await session.execute(overrides_stmt)).all()
    grants = {code for code, action in rows if action.value == 'grant'}
    revokes = {code for code, action in rows if action.value == 'revoke'}
    return sorted((role_codes | grants) - revokes)


ROLE_DEFAULTS = {
    # owner: full picture + ledger + can grant temp access
    'owner': [
        'view_owner_dashboard',
        'view_waste_map',
        'view_risk_alerts',
        'view_audit_ledger',
        'view_all_companies',
        'view_documents',
        'upload_documents',
        'export_reports',
        'approve_custom_reports',
        'manage_templates',
        'manage_company_users',
        'manage_permissions',
        'grant_temporary_access',
    ],
    # gm: dashboard view but no ledger, no user-management
    'gm': [
        'view_owner_dashboard',
        'view_waste_map',
        'view_risk_alerts',
        'view_documents',
        'upload_documents',
        'export_reports',
        'manage_templates',
    ],
    # manager: scoped to assigned company/branches only.
    # Sees tasks but not raw documents (auditor uploads + certifies for them).
    'manager': [
        'upload_documents',
        'view_tasks',
    ],
    # auditor: upload + certify + view raw documents ONLY.
    # NO analytics, NO waste map, NO risk alerts, NO ledger.
    'auditor': [
        'upload_documents',
        'view_documents',
        'view_tasks',
    ],
    # sysadmin: user + permission management, ledger read
    'admin': [
        'manage_company_users',
        'manage_permissions',
        'grant_temporary_access',
        'view_audit_ledger',
    ],
    # appowner: only the vendor-platform permissions, nothing else
    'appowner': [
        'app_owner_inventory',
        'app_owner_templates',
        'app_owner_maintenance',
    ],
}
