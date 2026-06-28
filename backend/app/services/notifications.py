from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.factories import get_notification_gateway, in_dnd_window
from app.models.entities import NotificationQueue


def should_send_now(severity: str) -> bool:
    if severity == 'critical':
        return not in_dnd_window()
    return False


async def queue_or_send_notification(session: AsyncSession, company_id, destination: str, message: str, severity: str = 'low') -> dict:
    settings = get_settings()
    if should_send_now(severity):
        return await get_notification_gateway().send(destination, message, severity)
    item = NotificationQueue(
        company_id=company_id,
        channel='whatsapp',
        destination=destination,
        message=message,
        severity=severity,
        status='queued',
        next_attempt_at=datetime.now(timezone.utc) + timedelta(minutes=5 if settings.deployment_mode == 'onpremise' else 0),
    )
    session.add(item)
    await session.flush()
    return {'status': 'queued', 'id': str(item.id), 'severity': severity}


async def flush_notification_queue(session: AsyncSession) -> list[dict]:
    now = datetime.now(timezone.utc)
    queued = (await session.execute(select(NotificationQueue).where(NotificationQueue.status == 'queued'))).scalars().all()
    results = []
    gateway = get_notification_gateway()
    for item in queued:
        if item.next_attempt_at and item.next_attempt_at > now:
            continue
        result = await gateway.send(item.destination, item.message, item.severity)
        item.status = 'sent'
        item.retry_count += 1
        results.append(result)
    await session.commit()
    return results
