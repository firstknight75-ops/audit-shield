"""Tamper-Proof Certificate for exported reports.

Per Phase 4 spec, every export carries:
- report_id (UUID, public-safe for the verify endpoint)
- ledger_hash_at_generation (SHA-256 hex)
- HMAC signature (deterministic, secret-key bound)
- non-sensitive payload summary

The verify endpoint uses these three values to confirm integrity
WITHOUT revealing the report's contents to a third-party verifier.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from uuid import uuid4

from app.core.config import get_settings


def _canonicalize(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def tamper_proof_certificate(
    payload: dict,
    ledger_hash_at_generation: str,
    report_id: str | None = None,
) -> dict:
    """Build a tamper-proof certificate for an export.

    Args:
        payload: Non-sensitive metadata about the export (title, rows_count, etc.).
                  Must NOT include the actual report rows.
        ledger_hash_at_generation: SHA-256 of the latest ledger entry at generation time.
        report_id: Optional pre-existing UUID; otherwise one is generated.

    Returns dict with: report_id, ledger_hash_at_generation, signature.
    """
    settings = get_settings()
    rid = report_id or str(uuid4())
    body = {
        'report_id': rid,
        'payload': payload,
        'ledger_hash_at_generation': ledger_hash_at_generation,
    }
    signature = hmac.new(
        settings.secret_key.encode(),
        _canonicalize(body).encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        'report_id': rid,
        'ledger_hash_at_generation': ledger_hash_at_generation,
        'signature': signature,
    }


def verify_certificate(
    report_id: str,
    ledger_hash_at_generation: str,
    signature: str,
    payload: dict,
) -> tuple[bool, str]:
    """Re-derive the HMAC signature and compare.

    Returns (valid, message). Used by the public /verify/{report_id} endpoint
    to confirm integrity without revealing the report's content.

    `payload` must be the EXACT non-sensitive metadata dict that was used
    when the certificate was generated (e.g. summary, company_id, output_code).
    """
    settings = get_settings()
    body = {
        'report_id': report_id,
        'payload': payload,
        'ledger_hash_at_generation': ledger_hash_at_generation,
    }
    expected = hmac.new(
        settings.secret_key.encode(),
        _canonicalize(body).encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False, 'tampered'
    return True, 'intact'
