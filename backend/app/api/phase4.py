from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.exports.engine import CORE_OUTPUT_TITLES, export_excel, export_pdf, export_png
from app.inventory.models import AppOwnerAuditEvent, ClientInventory, CraasRequest, PermissionTemplate
from app.models.entities import AnalyticsOutput, AuditLedger, User, WasteMapItem
from app.models.enums import UserRole
from app.schemas.phase4 import ExportRequest, WhatIfRequest
from app.services.access import get_accessible_company_ids, require_company_access
from app.services.i18n import tr
from app.templates.builder import SECTOR_PRESETS, build_template
from app.templates.versioning import bump_version, rollback_payload

router = APIRouter(tags=['phase4'])


@router.get('/manager/widgets')
async def manager_widgets(
    company_id: str = Query(...),
    branch_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.manager:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    if not await require_company_access(current_user, db, company_id, branch_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    return {
        'scope': {'company_id': company_id, 'branch_id': branch_id},
        'widgets': [
            {'code': 'budget_status', 'x': 0, 'y': 0},
            {'code': 'open_tasks', 'x': 1, 'y': 0},
            {'code': 'dept_quality_index', 'x': 0, 'y': 1},
            {'code': 'team_performance', 'x': 1, 'y': 1},
            {'code': 'pending_corrections', 'x': 0, 'y': 2},
        ],
    }


@router.post('/exports/run')
async def run_export(
    payload: ExportRequest,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_analytics')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))

    latest_ledger = (await db.execute(
        select(AuditLedger).where(AuditLedger.company_id == company_id).order_by(AuditLedger.created_at.desc())
    )).scalars().first()
    ledger_hash = latest_ledger.action_payload.get('entry_hash', 'GENESIS') if latest_ledger else 'GENESIS'
    rows = []
    if payload.output_code == 'waste_map':
        rows = [{'category': r.category, 'description': r.description, 'impact_score': r.impact_score, 'iqd_amount': r.iqd_amount} for r in (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == company_id))).scalars().all()]
    elif payload.output_code in {'true_picture', 'trust_index', 'risk_map', 'opportunity_map', 'action_plan', 'dashboards'}:
        analytics = (await db.execute(select(AnalyticsOutput).where(AnalyticsOutput.company_id == company_id).order_by(AnalyticsOutput.created_at.desc()))).scalars().first()
        rows = [analytics.payload] if analytics else []
    outdir = Path('exports')
    outdir.mkdir(exist_ok=True)
    title = CORE_OUTPUT_TITLES.get(payload.output_code, payload.output_code)
    filebase = outdir / f"{payload.output_code}-{company_id}"
    if payload.format == 'excel':
        path = export_excel(str(filebase.with_suffix('.xlsx')), title, rows, ledger_hash)
    elif payload.format == 'pdf':
        path = export_pdf(str(filebase.with_suffix('.pdf')), title, rows, ledger_hash)
    elif payload.format == 'png':
        path = export_png(str(filebase.with_suffix('.png.txt')), title, rows, ledger_hash)
    else:
        raise HTTPException(status_code=400, detail=tr('exports.unsupported_format', lang))
    return {'path': path, 'title': title}


@router.post('/what-if/run')
async def what_if_simulator(
    payload: WhatIfRequest,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_analytics')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    item = (await db.execute(select(WasteMapItem).where(WasteMapItem.id == payload.waste_map_item_id, WasteMapItem.company_id == company_id))).scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail=tr('whatif.waste_item_not_found', lang))
    recovered = item.iqd_amount * (payload.recovery_percent / 100.0)
    monthly = recovered / max(payload.horizon_months, 1)
    net = recovered - payload.manual_cost
    projection = []
    for m in range(1, payload.horizon_months + 1):
        projection.append({'month': m, 'cash_flow_delta': round(monthly, 2), 'net_profit_delta': round(net / payload.horizon_months, 2)})
    return {'waste_map_item_id': payload.waste_map_item_id, 'recovered_total': round(recovered, 2), 'manual_cost': payload.manual_cost, 'projection': projection}


@router.post('/what-if/export')
async def what_if_export(
    payload: WhatIfRequest,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_analytics')),
    db: AsyncSession = Depends(get_db),
):
    result = await what_if_simulator(payload, company_id, current_user, db)
    latest_ledger = (await db.execute(select(AuditLedger).where(AuditLedger.company_id == company_id).order_by(AuditLedger.created_at.desc()))).scalars().first()
    ledger_hash = latest_ledger.action_payload.get('entry_hash', 'GENESIS') if latest_ledger else 'GENESIS'
    outdir = Path('exports')
    outdir.mkdir(exist_ok=True)
    path = export_pdf(str(outdir / f"what-if-{company_id}.pdf"), CORE_OUTPUT_TITLES['what_if'], result['projection'], ledger_hash)
    return {'path': path}


# ── App Owner routes (platform-level, not company-scoped) ──────

@router.get('/appowner/clients')
async def appowner_clients(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    return (await db.execute(select(ClientInventory))).scalars().all()


@router.post('/appowner/clients/{client_id}/tier')
async def change_client_tier(client_id: str, body: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    client = (await db.execute(select(ClientInventory).where(ClientInventory.id == client_id))).scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail=tr('appowner.client_not_found', lang))
    old_tier = client.tier
    client.tier = body.get('tier', client.tier)
    client.user_cap = {'essential': 10, 'advanced': 20, 'elite': 50}.get(client.tier, client.user_cap)
    if old_tier != 'elite' and client.tier == 'elite' and client.deployment_mode == 'cloud':
        client.dedicated_database_url = f"postgresql://dedicated/{client.id}"
        client.tenant_schema = None
    db.add(AppOwnerAuditEvent(action='tier_change', target_client=client.name, details=f'{old_tier}->{client.tier}'))
    await db.commit()
    return {'message': tr('appowner.tier_updated', lang), 'dedicated_database_url': client.dedicated_database_url}


@router.get('/appowner/templates/presets')
async def template_presets(current_user: User = Depends(get_current_user)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    return SECTOR_PRESETS


@router.post('/appowner/templates')
async def create_template(body: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    payload = build_template(body['name'], body['sector'], body.get('widgets', []))
    template = PermissionTemplate(name=body['name'], sector=body['sector'], version=1, payload_json=payload)
    db.add(template)
    db.add(AppOwnerAuditEvent(action='template_created', target_client='global', details=body['name']))
    await db.commit()
    return {'message': tr('appowner.template_created', lang), 'payload': payload}


@router.post('/appowner/templates/{template_id}/push')
async def push_template(template_id: str, body: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    client = body.get('client_name', 'unknown')
    deployment_mode = body.get('deployment_mode', 'cloud')
    transport = 'vpn' if deployment_mode == 'onpremise' else 'cicd'
    db.add(AppOwnerAuditEvent(action='template_push', target_client=client, details=f'template_id={template_id};transport={transport}'))
    await db.commit()
    return {'message': tr('appowner.template_pushed', lang), 'transport': transport}


@router.post('/appowner/templates/{template_id}/rollback')
async def rollback_template(template_id: str, body: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    template = (await db.execute(select(PermissionTemplate).where(PermissionTemplate.id == template_id))).scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail=tr('appowner.template_not_found', lang))
    template.payload_json = rollback_payload(template.payload_json, body['previous_payload'])
    template.version = bump_version(template.version)
    db.add(AppOwnerAuditEvent(action='template_rollback', target_client='global', details=f'template_id={template_id}'))
    await db.commit()
    return {'message': tr('appowner.template_rolled_back', lang), 'version': template.version}


@router.get('/appowner/craas')
async def craas_queue(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    return (await db.execute(select(CraasRequest))).scalars().all()


@router.post('/appowner/craas')
async def create_craas_request(body: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    req = CraasRequest(client_name=body['client_name'], title=body['title'], status='quoted', quoted_price_iqd=body.get('quoted_price_iqd', 0), deployment_mode=body.get('deployment_mode', 'cloud'))
    db.add(req)
    db.add(AppOwnerAuditEvent(action='craas_queued', target_client=body['client_name'], details=body['title']))
    await db.commit()
    return {'message': tr('appowner.craas_queued', lang)}


@router.post('/appowner/clients/health-scan')
async def health_scan(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    rows = (await db.execute(select(ClientInventory))).scalars().all()
    for r in rows:
        r.last_health_check = 'ok'
    db.add(AppOwnerAuditEvent(action='health_scan', target_client='all', details='inventory-only health refresh'))
    await db.commit()
    return {'message': tr('appowner.health_scan_complete', lang), 'count': len(rows)}


@router.post('/appowner/ops/notify-health-event')
async def notify_health_event(body: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    event = body.get('event', 'container_down')
    target = body.get('target_client', 'unknown')
    db.add(AppOwnerAuditEvent(action='ops_alert', target_client=target, details=event))
    await db.commit()
    return {'message': tr('appowner.ops_event_registered', lang)}


@router.get('/appowner/maintenance')
async def appowner_maintenance(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if current_user.role != UserRole.appowner:
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    return (await db.execute(select(AppOwnerAuditEvent).order_by(AppOwnerAuditEvent.created_at.desc()))).scalars().all()
