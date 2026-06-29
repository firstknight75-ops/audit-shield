from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.entities import AnalyticsOutput, AuditLedger, DailyTask, Document, OCRExtraction, User, WasteMapItem
from app.models.enums import UserRole
from app.schemas.analytics import OwnerDashboardResponse, RecordTraceResponse
from app.services.access import get_accessible_company_ids, require_company_access
from app.services.i18n import tr

router = APIRouter(tags=['analytics'])


@router.post('/analytics/run/{company_id}')
async def trigger_analysis(
    company_id: str,
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('analytics.cannot_run_for_other_company', lang))
    from app.ai.orchestrator import _run_daily_analysis
    await _run_daily_analysis(company_id)
    return {'message': tr('analytics.daily_run_locally', lang)}


@router.get('/owner/dashboard', response_model=OwnerDashboardResponse)
async def owner_dashboard(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))

    row = (await db.execute(
        select(AnalyticsOutput)
        .where(AnalyticsOutput.company_id == company_id, AnalyticsOutput.output_type == 'owner_dashboard')
        .order_by(AnalyticsOutput.created_at.desc())
    )).scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail=tr('analytics.no_results_yet', lang))

    tasks = (await db.execute(select(DailyTask).where(DailyTask.company_id == company_id, DailyTask.task_type == 'ocr'))).scalars().all()
    total = len(tasks)
    on_time = len([t for t in tasks if t.status == 'done' and t.completed_at and t.completed_at <= t.due_at])
    demerits = sum(t.demerit_points for t in tasks)
    efficiency = ((on_time / total) * 100 if total else 100) - (demerits * 5)
    department_rows = (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == company_id))).scalars().all()
    breakdown = []
    by_category = {}
    for item in department_rows:
        by_category[item.category] = by_category.get(item.category, 0) + item.impact_score
    for k, v in by_category.items():
        breakdown.append({'department': k, 'score': v})
    payload = row.payload
    return OwnerDashboardResponse(
        monthly_waste=float(payload.get('monthly_waste', 0)),
        trust_index=int(payload.get('trust_index', 0)),
        critical_alerts=int(payload.get('critical_alerts', 0)),
        predicted_cash_outflow=float(payload.get('predicted_cash_outflow', 0)),
        auditor_efficiency=round(efficiency, 2),
        narrative=payload.get('owner_narrative', ''),
        department_breakdown=breakdown,
        findings=payload.get('findings', []),
    )


@router.get('/owner/dashboard/layer2')
async def owner_layer2(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    rows = (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == company_id))).scalars().all()
    return [{'category': r.category, 'description': r.description, 'impact_score': r.impact_score, 'iqd_amount': r.iqd_amount} for r in rows]


@router.get('/owner/dashboard/layer3')
async def owner_layer3(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    row = (await db.execute(
        select(AnalyticsOutput)
        .where(AnalyticsOutput.company_id == company_id, AnalyticsOutput.output_type == 'owner_dashboard')
        .order_by(AnalyticsOutput.created_at.desc())
    )).scalars().first()
    if not row:
        return []
    return row.payload.get('findings', [])


@router.get('/owner/dashboard/layer4/{document_id}', response_model=RecordTraceResponse)
async def owner_layer4(
    document_id: str,
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)
    if not await require_company_access(current_user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    document = (await db.execute(select(Document).where(Document.id == document_id, Document.company_id == company_id))).scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail=tr('analytics.document_not_found', lang))
    ocr = (await db.execute(select(OCRExtraction).where(OCRExtraction.document_id == document.id))).scalars().first()
    ledger_rows = (await db.execute(select(AuditLedger).where(AuditLedger.company_id == company_id).order_by(AuditLedger.created_at.asc()))).scalars().all()
    return RecordTraceResponse(
        document_id=str(document.id),
        filename=document.original_filename,
        ledger=[{'id': str(r.id), 'action_type': r.action_type, 'payload': r.action_payload} for r in ledger_rows if r.action_payload.get('document_id') == document_id or r.action_payload.get('extraction_id') == str(getattr(ocr, 'id', ''))],
        extracted_data=ocr.extracted_data if ocr else {},
    )


@router.get('/manager/dashboard')
async def manager_dashboard(
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

    doc_query = select(Document).where(Document.company_id == company_id)
    if branch_id:
        doc_query = doc_query.where(Document.branch_id == branch_id)
    docs = (await db.execute(doc_query)).scalars().all()
    allowed_doc_ids = {str(d.id) for d in docs}

    row = (await db.execute(
        select(AnalyticsOutput)
        .where(AnalyticsOutput.company_id == company_id, AnalyticsOutput.output_type == 'owner_dashboard')
        .order_by(AnalyticsOutput.created_at.desc())
    )).scalars().first()

    scoped_findings = []
    if row:
        for f in row.payload.get('findings', []):
            if str(f.get('document_id', '')) in allowed_doc_ids:
                scoped_findings.append(f)

    return {
        'company_id': company_id,
        'branch_id': branch_id,
        'documents_count': len(docs),
        'findings': scoped_findings[:20],
        'note': tr('manager.results_scoped', lang),
    }
