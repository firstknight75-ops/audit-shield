from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Branch, Company, CompanyGroup, Permission, RolePermission, Translation, User, UserCompanyAccess, UserPermissionOverride
from app.models.enums import CompanyTier, DeploymentMode, OverrideAction, PreferredLanguage, UserRole
from app.security.passwords import get_password_hash
from app.services.permissions import ROLE_DEFAULTS
from app.i18n.translations import TRANSLATIONS

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


async def seed(session: AsyncSession, deployment_mode: str = 'onpremise', group_name: str = 'مجموعة الفرات القابضة', tenant_schema: str | None = None):
    existing = (await session.execute(select(CompanyGroup))).scalar_one_or_none()
    if existing:
        return

    # ── Company Group ───────────────────────────────────────────
    group = CompanyGroup(
        name=group_name,
        tier=CompanyTier.advanced,
        deployment_mode=DeploymentMode(deployment_mode),
        tenant_schema=tenant_schema,
    )
    session.add(group)
    await session.flush()

    # ── Companies ───────────────────────────────────────────────
    company_a = Company(company_group_id=group.id, name='شركة الفرات للتجارة', sector='Trading')
    company_b = Company(company_group_id=group.id, name='مصنع الفرات للصناعات', sector='Manufacturing')
    session.add_all([company_a, company_b])
    await session.flush()

    # ── Branches ────────────────────────────────────────────────
    a1 = Branch(company_id=company_a.id, name='الفرع الأول', location='بغداد')
    a2 = Branch(company_id=company_a.id, name='الفرع الثاني', location='البصرة')
    b1 = Branch(company_id=company_b.id, name='فرع المصنع 1', location='أربيل')
    b2 = Branch(company_id=company_b.id, name='فرع المصنع 2', location='السليمانية')
    session.add_all([a1, a2, b1, b2])
    await session.flush()

    # ── Permissions ─────────────────────────────────────────────
    permission_map = {}
    for code, name, category in PERMISSIONS:
        perm = Permission(code=code, name=name, category=category)
        session.add(perm)
        await session.flush()
        permission_map[code] = perm

    for role_name, codes in ROLE_DEFAULTS.items():
        for code in codes:
            session.add(RolePermission(role=UserRole(role_name), permission_id=permission_map[code].id))

    # ── Users ───────────────────────────────────────────────────
    users = [
        ('owner@auditcore.local', 'Owner123!', 'Owner User', UserRole.owner, PreferredLanguage.ar),
        ('gm@auditcore.local', 'Gm123!', 'GM User', UserRole.gm, PreferredLanguage.ckb),
        ('manager@auditcore.local', 'Manager123!', 'Manager User', UserRole.manager, PreferredLanguage.ar),
        ('auditor@auditcore.local', 'Auditor123!', 'Auditor User', UserRole.auditor, PreferredLanguage.ckb),
        ('sysadmin@auditcore.local', 'Sysadmin123!', 'System Admin User', UserRole.admin, PreferredLanguage.ar),
        ('appowner@auditcore.local', 'Appowner123!', 'App Owner User', UserRole.appowner, PreferredLanguage.ckb),
    ]
    created = {}
    for email, password, full_name, role, language in users:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            company_group_id=group.id,
            is_active=True,
            preferred_language=language,
            last_activity_at=datetime.now(timezone.utc),
        )
        session.add(user)
        await session.flush()
        created[email] = user

    # ── User Company Access (default-deny, explicit grants) ─────
    for company in [company_a, company_b]:
        session.add(UserCompanyAccess(user_id=created['owner@auditcore.local'].id, company_id=company.id, branch_id=None, granted_by=created['sysadmin@auditcore.local'].id))
        session.add(UserCompanyAccess(user_id=created['gm@auditcore.local'].id, company_id=company.id, branch_id=None, granted_by=created['sysadmin@auditcore.local'].id))
    session.add(UserCompanyAccess(user_id=created['manager@auditcore.local'].id, company_id=company_a.id, branch_id=None, granted_by=created['owner@auditcore.local'].id))
    session.add(UserCompanyAccess(user_id=created['auditor@auditcore.local'].id, company_id=company_a.id, branch_id=a1.id, granted_by=created['owner@auditcore.local'].id))
    session.add(UserCompanyAccess(user_id=created['sysadmin@auditcore.local'].id, company_id=company_a.id, branch_id=None, granted_by=created['owner@auditcore.local'].id))
    session.add(UserCompanyAccess(user_id=created['sysadmin@auditcore.local'].id, company_id=company_b.id, branch_id=None, granted_by=created['owner@auditcore.local'].id))

    # ── Permission Overrides (scoped to company) ────────────────
    session.add(UserPermissionOverride(
        user_id=created['manager@auditcore.local'].id,
        permission_id=permission_map['view_waste_map'].id,
        company_id=company_a.id,
        action=OverrideAction.grant,
        reason='Scoped company A grant',
        is_active=True,
        created_by_user_id=created['owner@auditcore.local'].id,
    ))

    # ── Translation table rows (seeded from in-memory dict) ─────
    for key, translations in TRANSLATIONS.items():
        for lang_code, text in translations.items():
            lang_enum = PreferredLanguage(lang_code)
            session.add(Translation(key=key, language=lang_enum, text=text))

    await session.commit()
