from __future__ import annotations

import base64
import json
from hashlib import sha256

from cryptography.fernet import Fernet

from app.core.factories import get_key_backend


async def encrypt_bytes(tenant_or_company: str, file_id: str, data: bytes) -> bytes:
    key = await get_key_backend().get_key(tenant_or_company, file_id)
    fernet_key = base64.urlsafe_b64encode(sha256(key).digest())
    return Fernet(fernet_key).encrypt(data)


async def validate_encrypted_json_structure(data: bytes) -> bool:
    try:
        decoded = json.loads(data.decode('utf-8'))
    except Exception:
        return False
    return isinstance(decoded, (dict, list))
