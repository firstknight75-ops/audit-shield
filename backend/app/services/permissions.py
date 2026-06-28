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
    'owner': ['manage_users', 'manage_permissions', 'view_analytics', 'view_waste_map', 'view_risk_alerts', 'upload_documents', 'view_ledger'],
    'gm': ['view_analytics', 'view_waste_map', 'view_risk_alerts', 'upload_documents'],
    'manager': ['upload_documents', 'view_tasks'],
    'auditor': ['upload_documents', 'view_tasks', 'view_documents'],
    'admin': ['manage_users', 'manage_permissions', 'view_ledger'],
    'appowner': ['app_owner_inventory', 'app_owner_templates', 'app_owner_maintenance'],
}
