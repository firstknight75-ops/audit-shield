from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
from celery.schedules import crontab
from sqlalchemy import select, text, delete

from app.ai.anomaly import run_anomaly_detection
from app.ai.cross_reference import run_cross_reference
from app.ai.data_quality import run_data_quality
from app.ai.impact import findings_to_waste_items
from app.ai.narrative import generate_narrative
from app.ai.predictor import predict_next_month_cash_outflow
from app.core.celery_app import celery_app
from app.services.notifications import queue_or_send_notification
from app.db.session import SessionLocal
from app.models.entities import AnalyticsOutput, Document, OCRExtraction, RiskAlert, WasteMapItem
from app.services.ledger import append_ledger_entry


def compute_trust_index(findings: list[dict], total_docs: int) -> int:
    penalty = sum(8 if f.get('severity') == 'critical' else 3 for f in findings)
    score = 100 - penalty - max(0, (30 - total_docs))
    return max(0, min(100, score))


async def _queue_alert(session, company_id, severity: str, message: str):
    await queue_or_send_notification(session, company_id, 'owner', message, severity)


async def _run_daily_analysis(company_id: str):
    async with SessionLocal() as session:
        docs = (await session.execute(select(Document, OCRExtraction).join(OCRExtraction, OCRExtraction.document_id == Document.id).where(Document.company_id == company_id, OCRExtraction.status == 'certified'))).all()
        rows = []
        for doc, ocr in docs:
            data = ocr.extracted_data or {}
            rows.append({
                'document_id': str(doc.id),
                'invoice_number': data.get('invoice_number', ''),
                'date': data.get('date', ''),
                'amount': float(str(data.get('amount', 0)).replace(',', '') or 0),
                'vendor_name': data.get('vendor_name', ''),
                'serial': len(rows) + 1,
                'department': doc.metadata_json.get('department', 'المشتريات') if isinstance(doc.metadata_json, dict) else 'المشتريات',
                'branch': doc.metadata_json.get('branch', 'HQ') if isinstance(doc.metadata_json, dict) else 'HQ',
                'outflow_amount': float(str(data.get('bank_outflow_amount', data.get('amount', 0))).replace(',', '') or 0),
                'inventory_amount': float(str(data.get('inventory_amount', data.get('amount', 0))).replace(',', '') or 0),
            })
        df = pd.DataFrame(rows)
        procurement = df[['document_id', 'invoice_number', 'amount', 'department', 'branch']].copy() if not df.empty else pd.DataFrame()
        bank = df[['invoice_number', 'outflow_amount']].copy() if not df.empty else pd.DataFrame()
        inventory = df[['invoice_number', 'inventory_amount']].copy() if not df.empty else pd.DataFrame()
        findings = []
        findings.extend(run_data_quality(df))
        findings.extend(run_anomaly_detection(df))
        findings.extend(run_cross_reference(procurement, bank, inventory))
        invoice_to_doc = {str(r['invoice_number']): str(r['document_id']) for r in rows}
        for f in findings:
            if not f.get('document_id') and f.get('invoice_number') in invoice_to_doc:
                f['document_id'] = invoice_to_doc[f['invoice_number']]
        waste_items = findings_to_waste_items(findings)
        await session.execute(delete(WasteMapItem).where(WasteMapItem.company_id == company_id))
        await session.execute(delete(RiskAlert).where(RiskAlert.company_id == company_id))
        await session.execute(delete(AnalyticsOutput).where(AnalyticsOutput.company_id == company_id))
        total_waste = 0.0
        for item in waste_items:
            total_waste += item.get('iqd_amount', 0.0)
            session.add(WasteMapItem(company_id=company_id, category=item['category'], description=f"{item['description']} - {item.get('invoice_number') or ''} - {item.get('document_id') or ''}", impact_score=item['impact_score'], iqd_amount=int(item.get('iqd_amount', 0))))
            if item.get('severity') in {'critical', 'high'}:
                alert = RiskAlert(company_id=company_id, severity=item['severity'], message=f"{item['description']} بقيمة {int(item.get('iqd_amount', 0))} د.ع", status='open')
                session.add(alert)
                if item.get('severity') == 'critical':
                    await _queue_alert(session, company_id, 'critical', alert.message)
        pred_input = pd.DataFrame([{'month_index': i + 1, 'amount': r['amount']} for i, r in enumerate(rows[-12:])])
        pred = predict_next_month_cash_outflow(pred_input)
        trust = compute_trust_index(findings, len(rows))
        owner_narrative = generate_narrative('owner', {'monthly_waste': total_waste, 'trust_index': trust}, findings)
        manager_narrative = generate_narrative('manager', {'monthly_waste': total_waste, 'trust_index': trust}, findings)
        session.add(AnalyticsOutput(company_id=company_id, output_type='owner_dashboard', payload={'monthly_waste': total_waste, 'trust_index': trust, 'critical_alerts': len([f for f in findings if f.get('severity') == 'critical']), 'predicted_cash_outflow': pred['predicted_cash_outflow'], 'owner_narrative': owner_narrative, 'manager_narrative': manager_narrative, 'findings': findings}))
        await append_ledger_entry(session, company_id, None, 'daily_analysis_completed', {'findings_count': len(findings), 'trust_index': trust, 'monthly_waste': total_waste})
        await session.commit()


@celery_app.task(name='app.ai.orchestrator.run_daily_analysis')
def run_daily_analysis(company_id: str):
    import asyncio
    asyncio.run(_run_daily_analysis(company_id))


celery_app.conf.beat_schedule['run-daily-analysis'] = {
    'task': 'app.ai.orchestrator.run_daily_analysis',
    'schedule': crontab(hour=2, minute=0),
    'args': ('all',),
}
