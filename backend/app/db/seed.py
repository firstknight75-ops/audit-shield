from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.models import AppOwnerAuditEvent, ClientInventory, CraasRequest, PermissionTemplate
from app.models.entities import AnalyticsOutput, Branch, Company, DailyTask, Document, OCRExtraction, Permission, RiskAlert, RolePermission, User, UserPermissionOverride, WasteMapItem
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
        user = User(email=email, hashed_password=get_password_hash(password), full_name=full_name, role=role, branch_id=branch_id, company_id=company.id, is_active=True, last_activity_at=datetime.now(timezone.utc))
        session.add(user)
        await session.flush()
        created[email] = user

    session.add(UserPermissionOverride(user_id=created['auditor@auditcore.local'].id, permission_id=permission_map['view_waste_map'].id, action=OverrideAction.grant, reason='Temporary review access', expires_at=datetime.now(timezone.utc) + timedelta(days=7), is_active=True, created_by_user_id=created['owner@auditcore.local'].id))
    session.add(UserPermissionOverride(user_id=created['manager@auditcore.local'].id, permission_id=permission_map['view_documents'].id, action=OverrideAction.grant, reason='Operational need', is_active=True, created_by_user_id=created['owner@auditcore.local'].id))
    session.add(UserPermissionOverride(user_id=created['gm@auditcore.local'].id, permission_id=permission_map['manage_users'].id, action=OverrideAction.revoke, reason='Restricted for this tenant', is_active=True, created_by_user_id=created['owner@auditcore.local'].id))

    session.add(AnalyticsOutput(company_id=company.id, output_type='kpi', payload={'margin': 15}))
    session.add(WasteMapItem(company_id=company.id, category='process', description='Redundant handoff', impact_score=8, iqd_amount=6800000))
    session.add(RiskAlert(company_id=company.id, severity='high', message='Cash variance spike', status='open'))
    doc = Document(company_id=company.id, branch_id=branch.id, uploaded_by_user_id=created['auditor@auditcore.local'].id, original_filename='arabic-invoice.json', mime_type='application/json', file_size=24, encrypted_blob=b'encrypted', metadata_json={'encrypted': True, 'department': 'المشتريات', 'branch': 'HQ'})
    session.add(doc)
    await session.flush()
    session.add(OCRExtraction(document_id=doc.id, status='certified', extracted_data={'invoice_number': 'INV-2026-9001', 'date': '2026-06-28', 'amount': '12400000', 'vendor_name': 'شركة الرافدين', 'items_list': ['صنف 1', 'صنف 2'], 'inventory_amount': '5600000', 'bank_outflow_amount': '12400000'}, confidence_map={'invoice_number': 92, 'date': 90, 'amount': 58, 'vendor_name': 82, 'items_list': 88}, raw_text='فاتورة عربية تجريبية', page_count=1, processing_time_ms=1200))
    session.add(DailyTask(company_id=company.id, auditor_user_id=created['auditor@auditcore.local'].id, task_type='ocr', title='اعتماد فاتورة عربية', status='open', source_document_id=doc.id, due_at=datetime.now(timezone.utc) + timedelta(hours=4), sla_minutes=240, severity='normal'))
    for i in range(1, 12):
        amount = 1000000 + i * 100000
        meta = {'encrypted': True, 'department': 'المشتريات' if i % 2 else 'المخازن', 'branch': 'HQ'}
        extra = Document(company_id=company.id, branch_id=branch.id, uploaded_by_user_id=created['auditor@auditcore.local'].id, original_filename=f'invoice-{i}.json', mime_type='application/json', file_size=24, encrypted_blob=b'encrypted', metadata_json=meta)
        session.add(extra)
        await session.flush()
        session.add(OCRExtraction(document_id=extra.id, status='certified', extracted_data={'invoice_number': 'INV-2026-9001' if i == 2 else f'INV-2026-{9001+i}', 'date': '2026-06-28', 'amount': str(amount), 'vendor_name': 'شركة الرافدين', 'items_list': ['صنف'], 'inventory_amount': str(amount - 700000 if i == 3 else amount), 'bank_outflow_amount': str(amount)}, confidence_map={'invoice_number': 95, 'date': 93, 'amount': 90, 'vendor_name': 88, 'items_list': 86}, raw_text='فاتورة عربية', page_count=1, processing_time_ms=1100))

    session.add(ClientInventory(name=company.name, sector=company.sector, tier=company.tier.value, deployment_mode=company.deployment_mode.value, user_count=6, user_cap=20, health_url='http://localhost:8000/health', last_health_check='ok', last_backup='today', tenant_schema=tenant_schema))
    session.add(PermissionTemplate(name='Manufacturing Default', sector='Manufacturing', version=1, payload_json='{"widgets":["waste_map","risk_map"]}'))
    session.add(CraasRequest(client_name=company.name, title='تقرير مخصص للقطاع', status='pending', quoted_price_iqd=250000, deployment_mode=company.deployment_mode.value))
    session.add(AppOwnerAuditEvent(action='seed_inventory', target_client=company.name, details='seeded inventory record'))
    await session.commit()
