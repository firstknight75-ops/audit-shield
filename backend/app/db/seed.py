from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AnalyticsOutput, Branch, Company, Permission, RiskAlert, RolePermission, User, UserPermissionOverride, WasteMapItem
from app.models.enums import CompanyTier, DeploymentMode, OverrideAction, UserRole
from app.security.passwords import get_password_hash
from app.services.permissions import ROLE_DEFAULTS

PERMISSIONS = [
    ('manage_users', 'إدارة المستخدمين', 'company_admin'),
    ('manage_permissions', 'إدارة الصلاحيات', 'company_admin'),
    ('view_analytics', 'عرض التحليلات', 'analytics'),
    ('view_waste_map', 'عرض خريطة الهدر', 'analytics'),
    ('view_risk_alerts', 'عرض التنبيهات', 'analytics'),
    ('upload_documents', 'رفع المستندات', 'documents'),
    ('view_ledger', 'عرض السجل', 'ledger'),
    ('view_tasks', 'عرض المهام', 'tasks'),
    ('view_documents', 'عرض المستندات', 'documents'),
    ('app_owner_inventory', 'مخزون المنصة', 'app_owner'),
    ('app_owner_templates', 'قوالب المنصة', 'app_owner'),
    ('app_owner_maintenance', 'صيانة المنصة', 'app_owner'),
]


async def seed(session: AsyncSession, deployment_mode: str = 'onpremise', company_name: str = 'AuditCore Demo', tenant_schema: str | None = None):
    existing = (await session.execute(select(Company))).scalar_one_or_none()
    if existing:
        return
    company = Company(name=company_name, sector='Industrial', tier=CompanyTier.advanced, deployment_mode=DeploymentMode(deployment_mode), tenant_schema=tenant_schema)
    session.add(company)
    await session.flush()
    branch = Branch(company_id=company.id, name='HQ', location='Baghdad')
    session.add(branch)
    await session.flush()

    permission_map = {}
    for code, name, category in PERMISSIONS:
        perm = Permission(code=code, name=name, category=category)
        session.add(perm)
        await session.flush()
        permission_map[code] = perm

    for role_name, codes in ROLE_DEFAULTS.items():
        for code in codes:
            session.add(RolePermission(role=UserRole(role_name), permission_id=permission_map[code].id))

    users = [
        ('owner@auditcore.local', 'Owner123!', 'Owner User', UserRole.owner),
        ('gm@auditcore.local', 'Gm123!', 'GM User', UserRole.gm),
        ('manager@auditcore.local', 'Manager123!', 'Manager User', UserRole.manager),
        ('auditor@auditcore.local', 'Auditor123!', 'Auditor User', UserRole.auditor),
        ('sysadmin@auditcore.local', 'Sysadmin123!', 'System Admin User', UserRole.admin),
        ('appowner@auditcore.local', 'Appowner123!', 'App Owner User', UserRole.appowner),
    ]
    created = {}
    for email, password, full_name, role in users:
        branch_id = None if role == UserRole.appowner else branch.id
        company_id = company.id
        user = User(email=email, hashed_password=get_password_hash(password), full_name=full_name, role=role, branch_id=branch_id, company_id=company_id, is_active=True, last_activity_at=datetime.now(timezone.utc))
        session.add(user)
        await session.flush()
        created[email] = user

    session.add(UserPermissionOverride(user_id=created['auditor@auditcore.local'].id, permission_id=permission_map['view_waste_map'].id, action=OverrideAction.grant, reason='Temporary review access', expires_at=datetime.now(timezone.utc) + timedelta(days=7), is_active=True, created_by_user_id=created['owner@auditcore.local'].id))
    session.add(UserPermissionOverride(user_id=created['manager@auditcore.local'].id, permission_id=permission_map['view_documents'].id, action=OverrideAction.grant, reason='Operational need', is_active=True, created_by_user_id=created['owner@auditcore.local'].id))
    session.add(UserPermissionOverride(user_id=created['gm@auditcore.local'].id, permission_id=permission_map['manage_users'].id, action=OverrideAction.revoke, reason='Restricted for this tenant', is_active=True, created_by_user_id=created['owner@auditcore.local'].id))

    session.add(AnalyticsOutput(company_id=company.id, output_type='kpi', payload={'margin': 15}))
    session.add(WasteMapItem(company_id=company.id, category='process', description='Redundant handoff', impact_score=8))
    session.add(RiskAlert(company_id=company.id, severity='high', message='Cash variance spike', status='open'))
    await session.commit()
