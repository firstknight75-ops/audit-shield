from __future__ import annotations

import hashlib
import hmac
import json

from app.core.config import get_settings


def tamper_proof_certificate(payload: dict, ledger_hash_at_generation: str) -> dict:
    settings = get_settings()
    body = json.dumps({**payload, 'ledger_hash_at_generation': ledger_hash_at_generation}, ensure_ascii=False, sort_keys=True)
    signature = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).hexdigest()
    return {'ledger_hash_at_generation': ledger_hash_at_generation, 'signature': signature}
