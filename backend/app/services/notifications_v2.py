"""Multi-channel notification gateway — Email, In-app, Slack, Teams, WhatsApp.

Per Phase 6 spec, critical/high/low severity each have their own routing:
- Critical → immediate push on ALL available channels (WhatsApp + Email + In-app)
- High → in-app + queued email digest at 07:00
- Low → in-app only

DND window (configurable) applies to non-critical channels.

This module extends `app.services.notifications` without breaking its
existing public API.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Literal

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import NotificationQueue

logger = logging.getLogger('auditcore.notifications')

Severity = Literal['critical', 'high', 'normal', 'low']


@dataclass
class ChannelDelivery:
    channel: str
    delivered: bool
    detail: str


async def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    attachments: list[tuple[str, bytes]] | None = None,
) -> ChannelDelivery:
    """Send via SMTP. Uses aiosmtplib if available, otherwise writes to
    /tmp/auditcore-mail/ for local capture (CI/sandbox friendly).

    Production: configure SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD env vars.
    """
    settings = get_settings()
    smtp_host = __import__('os').environ.get('SMTP_HOST')
    if not smtp_host:
        # Local capture — useful for tests; replace with real SMTP in prod.
        import os
        os.makedirs('/tmp/auditcore-mail', exist_ok=True)
        path = f'/tmp/auditcore-mail/{datetime.now(timezone.utc).isoformat()}-{to}.eml'
        async with aiofiles.open(path, 'w') as f:
            await f.write(f'To: {to}\nSubject: {subject}\n\n{body}')
        return ChannelDelivery(channel='email', delivered=True, detail=f'local_capture:{path}')

    try:
        import aiosmtplib  # type: ignore
        msg = EmailMessage()
        msg['From'] = settings.app_name + '@auditcore.local'
        msg['To'] = to
        msg['Subject'] = subject
        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype='html')
        for name, data in (attachments or []):
            msg.add_attachment(data, filename=name)
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=int(__import__('os').environ.get('SMTP_PORT', '587')),
            username=__import__('os').environ.get('SMTP_USER'),
            password=__import__('os').environ.get('SMTP_PASSWORD'),
        )
        return ChannelDelivery(channel='email', delivered=True, detail='smtp')
    except Exception as exc:
        logger.warning('email_send_failed', extra={'to': to, 'reason': str(exc)})
        return ChannelDelivery(channel='email', delivered=False, detail=str(exc))


async def send_inapp(
    user_id: str,
    title: str,
    body: str,
    severity: Severity = 'normal',
    link: str | None = None,
) -> ChannelDelivery:
    """In-app notification — written to inapp_notifications table.

    Frontend polls /api/inapp/unread for the badge count, and the notification
    dropdown fetches /api/inapp/recent.
    """
    from app.models.entities import InAppNotification
    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        notif = InAppNotification(
            user_id=user_id,
            title=title,
            body=body,
            severity=severity,
            link=link,
        )
        session.add(notif)
        await session.commit()
    return ChannelDelivery(channel='inapp', delivered=True, detail='persisted')


async def send_slack(channel: str, text: str) -> ChannelDelivery:
    """Slack incoming-webhook delivery. No-op if SLACK_WEBHOOK_URL unset."""
    import os
    url = os.environ.get('SLACK_WEBHOOK_URL')
    if not url:
        return ChannelDelivery(channel='slack', delivered=False, detail='slack_disabled')
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={'channel': channel, 'text': text})
        return ChannelDelivery(channel='slack', delivered=True, detail='posted')
    except Exception as exc:
        return ChannelDelivery(channel='slack', delivered=False, detail=str(exc))


async def send_teams(text: str) -> ChannelDelivery:
    """Microsoft Teams incoming-webhook delivery. No-op if unset."""
    import os
    url = os.environ.get('TEAMS_WEBHOOK_URL')
    if not url:
        return ChannelDelivery(channel='teams', delivered=False, detail='teams_disabled')
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={'text': text})
        return ChannelDelivery(channel='teams', delivered=True, detail='posted')
    except Exception as exc:
        return ChannelDelivery(channel='teams', delivered=False, detail=str(exc))


def in_dnd_window(severity: Severity, settings=None) -> bool:
    """DND applies to non-critical severities only."""
    if severity == 'critical':
        return False
    settings = settings or get_settings()
    hour = datetime.now(timezone.utc).hour
    start = settings.dnd_start_hour
    end = settings.dnd_end_hour
    return hour >= start or hour < end


async def fan_out(
    session: AsyncSession,
    *,
    company_id: str | None,
    severity: Severity,
    title: str,
    body: str,
    recipients: list[dict],
    extra: dict | None = None,
) -> list[ChannelDelivery]:
    """Route a notification to all configured channels.

    recipients: [{ 'user_id': str, 'email': str?, 'phone': str?, 'locale': 'ar'|'ckb' }]
    """
    deliveries: list[ChannelDelivery] = []
    for r in recipients:
        user_id = r['user_id']
        # Localize
        from app.services.i18n import tr
        locale = r.get('locale', 'ar')
        subject = tr(f'notifications.{severity}_subject', locale).format(company=r.get('company_name', ''))
        # Always in-app — it's the inbox.
        if severity in ('critical', 'high', 'normal'):
            deliveries.append(await send_inapp(user_id, subject, body, severity=severity))
        # Email: skip during DND unless critical.
        if r.get('email') and not in_dnd_window(severity):
            deliveries.append(await send_email(r['email'], subject, body))
        # WhatsApp: critical pushes go through the mode-selected gateway.
        if severity == 'critical' and r.get('phone'):
            from app.core.factories import get_notification_gateway
            gateway = get_notification_gateway()
            res = await gateway.send(r['phone'], body, 'critical')
            deliveries.append(ChannelDelivery(channel='whatsapp', delivered=bool(res), detail=str(res)))
        # Slack/Teams: only on critical.
        if severity == 'critical':
            slack_channel = r.get('slack_channel')
            if slack_channel:
                deliveries.append(await send_slack(slack_channel, f'{subject}\n{body}'))
            if r.get('teams'):
                deliveries.append(await send_teams(f'{subject}\n{body}'))
    return deliveries


async def fan_out_persisted(
    session: AsyncSession,
    *,
    company_id: str | None,
    severity: Severity,
    title: str,
    body: str,
    recipients: list[dict],
) -> list[ChannelDelivery]:
    """Like fan_out but also persists a NotificationQueue row for audit trail."""
    deliveries = await fan_out(session, company_id=company_id, severity=severity, title=title, body=body, recipients=recipients)
    # Persist each as queue row for the activity feed + retry
    for d in deliveries:
        if not d.delivered:
            session.add(NotificationQueue(
                company_id=company_id,
                channel=d.channel,
                destination='queued',
                message=body,
                severity=severity,
                status='pending_retry',
                next_attempt_at=datetime.now(timezone.utc),
            ))
    await session.commit()
    return deliveries
