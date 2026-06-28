from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from app.core.config import get_settings


class KeyBackend:
    async def get_key(self, company_or_tenant: str, file_id: str) -> bytes:
        raise NotImplementedError


class OnPremiseKeyBackend(KeyBackend):
    async def get_key(self, company_or_tenant: str, file_id: str) -> bytes:
        settings = get_settings()
        return sha256(f"{settings.company_master_key}:{company_or_tenant}:{file_id}".encode()).digest()


class VaultKeyBackend(KeyBackend):
    async def get_key(self, company_or_tenant: str, file_id: str) -> bytes:
        settings = get_settings()
        material = f"{settings.vault_url}:{settings.vault_token}:{company_or_tenant}:{file_id}"
        return sha256(material.encode()).digest()


class NotificationGateway:
    async def send(self, destination: str, message: str, severity: str = 'low') -> dict:
        return {'destination': destination, 'message': message, 'severity': severity, 'status': 'queued', 'gateway': 'base'}


class BaileysGateway(NotificationGateway):
    async def send(self, destination: str, message: str, severity: str = 'low') -> dict:
        return {'destination': destination, 'message': message, 'severity': severity, 'status': 'queued', 'gateway': 'baileys'}


class WhatsAppCloudGateway(NotificationGateway):
    async def send(self, destination: str, message: str, severity: str = 'low') -> dict:
        return {'destination': destination, 'message': message, 'severity': severity, 'status': 'queued', 'gateway': 'whatsapp-cloud'}


@dataclass
class BackupTarget:
    name: str


REGISTRY = {
    'onpremise': {
        'key_backend': OnPremiseKeyBackend,
        'notification_gateway': BaileysGateway,
        'backup_target': lambda: BackupTarget(name='local-disk'),
    },
    'cloud': {
        'key_backend': VaultKeyBackend,
        'notification_gateway': WhatsAppCloudGateway,
        'backup_target': lambda: BackupTarget(name='object-storage'),
    },
}


def _mode_registry():
    return REGISTRY[get_settings().deployment_mode]


def get_key_backend() -> KeyBackend:
    return _mode_registry()['key_backend']()


def get_notification_gateway() -> NotificationGateway:
    return _mode_registry()['notification_gateway']()


def get_backup_target() -> BackupTarget:
    return _mode_registry()['backup_target']()


def in_dnd_window(start: int = 23, end: int = 6) -> bool:
    hour = datetime.now().hour
    return hour >= start or hour < end
