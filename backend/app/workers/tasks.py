from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.entities import DailyTask, Document, OCRExtraction, User
from app.models.enums import UserRole
from app.services.encryption import decrypt_bytes_to_memory
from app.services.ledger import append_ledger_entry
from app.services.ocr import build_extraction_payload, parse_document_bytes

SLA = {
    'ocr': 240,
    'statements': 1440,
    'reversals': 120,
    'branch_backlog': 240,
}


@celery_app.task(name='app.workers.tasks.process_ocr_document')
def process_ocr_document(document_id: str):
    import asyncio
    asyncio.run(_process_ocr_document(document_id))


async def _process_ocr_document(document_id: str):
    async with SessionLocal() as session:
        document = (await session.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
        extraction = (await session.execute(select(OCRExtraction).where(OCRExtraction.document_id == document_id))).scalar_one_or_none()
        if not document or not extraction:
            return
        decrypted = await decrypt_bytes_to_memory(str(document.company_id), str(document.id), document.encrypted_blob)
        text, page_count, processing_time_ms = parse_document_bytes(decrypted, document.mime_type)
        extracted_data, confidence_map = build_extraction_payload(text)
        extraction.status = 'pending'
        extraction.extracted_data = extracted_data
        extraction.confidence_map = confidence_map
        extraction.raw_text = text
        extraction.page_count = page_count
        extraction.processing_time_ms = processing_time_ms
        await append_ledger_entry(session, document.company_id, document.uploaded_by_user_id, 'ocr_processed', {'document_id': str(document.id), 'page_count': page_count, 'processing_time_ms': processing_time_ms})
        await session.commit()


@celery_app.task(name='app.workers.tasks.generate_daily_tasks')
def generate_daily_tasks():
    import asyncio
    asyncio.run(_generate())


async def _generate():
    now = datetime.now(ZoneInfo('Asia/Baghdad')).astimezone(timezone.utc)
    async with SessionLocal() as session:
        auditors = (await session.execute(select(User).where(User.role == UserRole.auditor, User.is_active.is_(True)))).scalars().all()
        pending = (await session.execute(select(OCRExtraction).where(OCRExtraction.status == 'pending'))).scalars().all()
        for i, ext in enumerate(pending):
            if not auditors:
                break
            auditor = auditors[i % len(auditors)]
            exists = (await session.execute(select(DailyTask).where(DailyTask.source_document_id == ext.document_id, DailyTask.task_type == 'ocr', DailyTask.status == 'open'))).scalars().first()
            if exists:
                continue
            task = DailyTask(company_id=auditor.company_id, auditor_user_id=auditor.id, task_type='ocr', title=f'اعتماد مستند {ext.document_id}', status='open', source_document_id=ext.document_id, due_at=now + timedelta(minutes=SLA['ocr']), sla_minutes=SLA['ocr'], severity='normal')
            session.add(task)
            await append_ledger_entry(session, auditor.company_id, None, 'task_created', {'task_type': 'ocr', 'document_id': str(ext.document_id)})
        await session.commit()


@celery_app.task(name='app.workers.tasks.apply_sla_demerits')
def apply_sla_demerits():
    import asyncio
    asyncio.run(_apply())


async def _apply():
    now = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        tasks = (await session.execute(select(DailyTask).where(DailyTask.status == 'open', DailyTask.due_at < now - timedelta(minutes=15), DailyTask.demerit_points == 0))).scalars().all()
        for task in tasks:
            task.demerit_points = 3 if task.severity == 'critical' else 1
            await append_ledger_entry(session, task.company_id, task.auditor_user_id, 'sla_demerit_applied', {'task_id': str(task.id), 'points': task.demerit_points})
        await session.commit()



@celery_app.task(name='app.workers.tasks.flush_notification_queue_task')
def flush_notification_queue_task():
    import asyncio
    asyncio.run(_flush_notifications())


async def _flush_notifications():
    from app.services.notifications import flush_notification_queue
    async with SessionLocal() as session:
        await flush_notification_queue(session)
