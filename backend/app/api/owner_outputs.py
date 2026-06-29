"""Owner Outputs — the 7 deliverables every cycle.

This router exposes each of the 7 outputs as a first-class endpoint,
not a derived field on a dashboard card.

1. الصورة الحقيقية (The True Picture) — /owner/picture
2. مؤشر الموثوقية (Trust Index)     — /owner/trust-index
3. خريطة الهدر (Waste Map)           — /owner/waste-map  (delegates to /analytics/owner/dashboard/layer2)
4. خريطة المخاطر (Risk Map)         — /owner/risk-map
5. خريطة الفرص (Opportunity Map)     — /owner/opportunity-map
6. خطة العمل (Action Plan)           — /owner/action-plan
7. لوحات القيادة (Role dashboards)   — see /manager/dashboard, /owner/dashboard

Activation tracker:
   /owner/activation
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.entities import (
    AnalyticsOutput,
    AuditLedger,
    Company,
    CompanyGroup,
    Document,
    OCRExtraction,
    RiskAlert,
    User,
    WasteMapItem,
)
from app.services.access import require_company_access
from app.services.action_plan import (
    action_items_to_dict,
    build_adaptation_path,
    build_change_path,
)
from app.services.activation import compute_activation_status
from app.services.i18n import tr
from app.services.ledger import append_ledger_entry
from app.services.opportunity_map import (
    build_opportunity_map,
    opportunities_to_dict,
    total_upside_iqd,
)
from app.services.portfolio import CompanyPortfolioEntry, build_portfolio
from app.services.trust_index import (
    merge_findings_into_trust,
    trust_index_to_dict,
)

router = APIRouter(prefix='/owner', tags=['owner-outputs'])


# ── Shared helpers ───────────────────────────────────────────────────
async def _ensure_company_access(user: User, db: AsyncSession, company_id: str) -> str:
    lang = user.preferred_language.value if hasattr(user.preferred_language, 'value') else str(user.preferred_language)
    if not await require_company_access(user, db, company_id):
        raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
    return lang


async def _documents_for_company(db: AsyncSession, company_id: str) -> list[dict]:
    rows = (await db.execute(select(Document).where(Document.company_id == company_id))).scalars().all()
    return [
        {
            'document_id': str(d.id),
            'invoice_number': (d.metadata_json or {}).get('invoice_number'),
            'date': (d.metadata_json or {}).get('date'),
            'amount': (d.metadata_json or {}).get('amount'),
            'vendor_name': (d.metadata_json or {}).get('vendor_name'),
            'branch_id': str(d.branch_id) if d.branch_id else None,
            'branch_name': (d.metadata_json or {}).get('branch_name'),
        }
        for d in rows
    ]


# ── 1. الصورة الحقيقية (The True Picture) ───────────────────────────
@router.get('/picture')
async def owner_picture(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)

    row = (await db.execute(
        select(AnalyticsOutput)
        .where(AnalyticsOutput.company_id == company_id, AnalyticsOutput.output_type == 'owner_dashboard')
        .order_by(AnalyticsOutput.created_at.desc())
    )).scalars().first()

    if not row:
        return {
            'title': tr('owner.truth_picture', lang) if 'owner.truth_picture' in tr.__doc__ else 'الصورة الحقيقية',
            'available': False,
            'message': tr('analytics.no_results_yet', lang),
        }

    payload = row.payload or {}
    return {
        'title': 'الصورة الحقيقية',
        'available': True,
        'monthly_waste_iqd': payload.get('monthly_waste', 0),
        'trust_index_score': int(payload.get('trust_index', 0)),
        'critical_alerts': int(payload.get('critical_alerts', 0)),
        'predicted_cash_outflow_iqd': payload.get('predicted_cash_outflow', 0),
        'auditor_efficiency': payload.get('auditor_efficiency'),
        'narrative': payload.get('owner_narrative', ''),
        'findings_count': len(payload.get('findings', [])),
        'generated_at': row.created_at.isoformat() if row.created_at else None,
    }


# ── 2. مؤشر الموثوقية (Trust Index) — first-class deliverable ────────
@router.get('/trust-index')
async def owner_trust_index(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)

    documents = await _documents_for_company(db, company_id)
    total = len(documents)
    ocr_rows = (await db.execute(
        select(OCRExtraction).join(Document, Document.id == OCRExtraction.document_id).where(Document.company_id == company_id)
    )).scalars().all()
    certified_count = sum(1 for o in ocr_rows if o.status == 'certified')

    # Build findings-shaped list from raw OCR confidence data
    findings: list[dict] = []
    for d in documents:
        for field in ('invoice_number', 'date', 'amount', 'vendor_name'):
            if not d.get(field):
                findings.append({'type': 'missing_fields', 'document_id': d['document_id'], 'missing_fields': [field]})
    # duplicate detection
    seen: dict[str, str] = {}
    for d in documents:
        inv = d.get('invoice_number')
        if inv and inv in seen:
            findings.append({'type': 'duplicate_invoice', 'document_id': d['document_id'], 'invoice_number': inv})
        elif inv:
            seen[inv] = d['document_id']

    comp = merge_findings_into_trust(findings, total, certified_count)

    # Ledger the trust check (immutable record)
    await append_ledger_entry(
        db,
        company_id=company_id,
        actor_user_id=current_user.id,
        action_type='trust_index_check',
        action_payload={'score': comp.score, 'level': comp.level, 'documents': total},
    )
    await db.commit()

    return {
        'title': tr('trust_index.title', lang),
        'subtitle': tr('trust_index.subtitle', lang),
        **trust_index_to_dict(comp),
        'last_run': datetime.now(timezone.utc).isoformat(),
    }


# ── 3. خريطة الهدر (Waste Map) — explicit endpoint ───────────────────
@router.get('/waste-map')
async def owner_waste_map(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)
    rows = (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == company_id))).scalars().all()
    return {
        'title': 'خريطة الهدر',
        'items': [
            {
                'category': r.category,
                'description': r.description,
                'impact_score': r.impact_score,
                'iqd_amount': r.iqd_amount,
            }
            for r in rows
        ],
        'total_iqd': sum(r.iqd_amount for r in rows),
    }


# ── 4. خريطة المخاطر (Risk Map) ─────────────────────────────────────
@router.get('/risk-map')
async def owner_risk_map(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)
    rows = (await db.execute(select(RiskAlert).where(RiskAlert.company_id == company_id))).scalars().all()
    by_severity: dict[str, int] = {}
    for r in rows:
        by_severity[r.severity] = by_severity.get(r.severity, 0) + 1
    return {
        'title': 'خريطة المخاطر',
        'alerts': [
            {
                'id': str(r.id),
                'severity': r.severity,
                'message': r.message,
                'status': r.status,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        'count_by_severity': by_severity,
        'total_open': sum(1 for r in rows if r.status == 'open'),
    }


# ── 5. خريطة الفرص (Opportunity Map) ─────────────────────────────────
@router.get('/opportunity-map')
async def owner_opportunity_map(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)

    documents = await _documents_for_company(db, company_id)
    waste_rows = (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == company_id))).scalars().all()
    waste_items = [
        {'category': w.category, 'description': w.description, 'impact_score': w.impact_score, 'iqd_amount': w.iqd_amount}
        for w in waste_rows
    ]
    opps = build_opportunity_map(documents, waste_items)
    total = total_upside_iqd(opps)

    await append_ledger_entry(
        db,
        company_id=company_id,
        actor_user_id=current_user.id,
        action_type='opportunity_map_check',
        action_payload={'items_count': len(opps), 'total_upside_iqd': total},
    )
    await db.commit()

    return {
        'title': tr('opportunity_map.title', lang),
        'subtitle': tr('opportunity_map.subtitle', lang),
        'items': opportunities_to_dict(opps),
        'total_upside_iqd': total,
    }


# ── 6. خطة العمل (Action Plan) ───────────────────────────────────────
@router.get('/action-plan')
async def owner_action_plan(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)

    waste_rows = (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == company_id))).scalars().all()
    waste_items = [
        {'category': w.category, 'description': w.description, 'impact_score': w.impact_score, 'iqd_amount': w.iqd_amount}
        for w in waste_rows
    ]
    # pull trust level for adaptation path
    documents = await _documents_for_company(db, company_id)
    total_docs = len(documents)
    missing_count = sum(
        1
        for d in documents
        for f in ('invoice_number', 'date', 'amount', 'vendor_name')
        if not d.get(f)
    )
    slots = max(total_docs * 4, 1)
    coverage_pct = max(0.0, 100.0 - (missing_count / slots * 100.0))
    trust_level = 'high' if coverage_pct >= 80 else ('medium' if coverage_pct >= 60 else 'low')

    change = build_change_path(waste_items)
    adaptation = build_adaptation_path(waste_items, trust_level, coverage_pct)

    await append_ledger_entry(
        db,
        company_id=company_id,
        actor_user_id=current_user.id,
        action_type='action_plan_generated',
        action_payload={
            'change_items': len(change),
            'adaptation_items': len(adaptation),
            'change_iqd_total': sum(a.estimated_iqd for a in change),
        },
    )
    await db.commit()

    return {
        'title': tr('action_plan.title', lang),
        'subtitle': tr('action_plan.subtitle', lang),
        'change_path': {
            'label': tr('action_plan.change_path', lang),
            'items': action_items_to_dict(change),
        },
        'adaptation_path': {
            'label': tr('action_plan.adaptation_path', lang),
            'items': action_items_to_dict(adaptation),
        },
        'trust_context': {
            'coverage_pct': round(coverage_pct, 2),
            'trust_level': trust_level,
        },
    }


# ── Activation tracker (48h) ────────────────────────────────────────
@router.get('/activation')
async def owner_activation(
    company_id: str = Query(...),
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    lang = await _ensure_company_access(current_user, db, company_id)

    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail=tr('analytics.document_not_found', lang))
    group = (await db.execute(select(CompanyGroup).where(CompanyGroup.id == company.company_group_id))).scalar_one_or_none()
    install_at = group.created_at if group else datetime.now(timezone.utc)

    first_upload = (await db.execute(
        select(Document).where(Document.company_id == company_id).order_by(Document.created_at.asc())
    )).scalars().first()
    first_upload_at = first_upload.created_at if first_upload else None

    first_certified = (await db.execute(
        select(OCRExtraction).join(Document, Document.id == OCRExtraction.document_id)
        .where(Document.company_id == company_id, OCRExtraction.certified_at.is_not(None))
        .order_by(OCRExtraction.certified_at.asc())
    )).scalars().first()
    first_certified_at = first_certified.certified_at if first_certified else None

    first_dashboard = (await db.execute(
        select(AnalyticsOutput)
        .where(AnalyticsOutput.company_id == company_id, AnalyticsOutput.output_type == 'owner_dashboard')
        .order_by(AnalyticsOutput.created_at.asc())
    )).scalars().first()
    first_dashboard_at = first_dashboard.created_at if first_dashboard else None

    status = compute_activation_status(
        install_at=install_at,
        first_upload_at=first_upload_at,
        first_certified_at=first_certified_at,
        first_dashboard_at=first_dashboard_at,
    )
    return {
        'title': tr('activation.title', lang),
        'subtitle': tr('activation.subtitle', lang),
        **status.to_dict(lang),
        'within_48h_label': tr('activation.within_48h', lang) if status.within_48h else tr('activation.exceeded', lang),
    }


# ── Portfolio (multi-company owner view, never blended silently) ─────
@router.get('/portfolio')
async def owner_portfolio(
    current_user: User = Depends(require_permission('view_owner_dashboard')),
    db: AsyncSession = Depends(get_db),
):
    from app.services.access import get_accessible_company_ids

    company_ids = await get_accessible_company_ids(current_user, db)
    if not company_ids:
        return {
            'title': tr('portfolio.title', current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else 'ar'),
            'companies': [],
            'message': tr('portfolio.no_companies', current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else 'ar'),
        }

    entries: list[CompanyPortfolioEntry] = []
    for cid in company_ids:
        company = (await db.execute(select(Company).where(Company.id == cid))).scalar_one_or_none()
        if not company:
            continue
        waste_rows = (await db.execute(select(WasteMapItem).where(WasteMapItem.company_id == cid))).scalars().all()
        risk_rows = (await db.execute(select(RiskAlert).where(RiskAlert.company_id == cid))).scalars().all()
        documents = await _documents_for_company(db, cid)
        # simple trust index per company
        findings = []
        for d in documents:
            for f in ('invoice_number', 'date', 'amount', 'vendor_name'):
                if not d.get(f):
                    findings.append({'type': 'missing_fields', 'document_id': d['document_id'], 'missing_fields': [f]})
        comp = merge_findings_into_trust(findings, len(documents), 0)
        opps = build_opportunity_map(documents, [{'category': w.category, 'iqd_amount': w.iqd_amount} for w in waste_rows])
        entries.append(CompanyPortfolioEntry(
            company_id=str(company.id),
            company_name=company.name,
            trust_index_score=comp.score,
            monthly_waste_iqd=sum(w.iqd_amount for w in waste_rows),
            critical_alerts=sum(1 for r in risk_rows if r.severity == 'critical'),
            opportunity_iqd=total_upside_iqd(opps),
            risk_alerts=len(risk_rows),
            documents_total=len(documents),
        ))

    return {
        'title': tr('portfolio.title', current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else 'ar'),
        'subtitle': tr('portfolio.subtitle', current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else 'ar'),
        **build_portfolio(entries),
    }
