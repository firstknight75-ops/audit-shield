from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLedger
from app.services.i18n import tr


def _stable_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _hash(previous_hash: str, entry: dict) -> str:
    return hashlib.sha256((previous_hash + _stable_json(entry)).encode('utf-8')).hexdigest()


async def append_ledger_entry(session: AsyncSession, company_id, actor_user_id, action_type: str, action_payload: dict) -> AuditLedger:
    previous = (await session.execute(select(AuditLedger).where(AuditLedger.company_id == company_id).order_by(AuditLedger.created_at.desc()))).scalars().first()
    previous_hash = previous.action_payload.get('entry_hash', 'GENESIS') if previous else 'GENESIS'
    entry_id = str(uuid4())
    body = {
        'entry_id': entry_id,
        'company_id': str(company_id),
        'actor_user_id': str(actor_user_id) if actor_user_id else None,
        'action_type': action_type,
        'action_payload': action_payload,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    entry_hash = _hash(previous_hash, body)
    ledger = AuditLedger(id=entry_id, company_id=company_id, actor_user_id=actor_user_id, action_type=action_type, action_payload={**action_payload, 'entry_hash': entry_hash, 'previous_hash': previous_hash, 'entry_body': body})
    session.add(ledger)
    await session.flush()
    return ledger


async def append_reverse_entry(
    session: AsyncSession,
    company_id,
    actor_user_id,
    target_entry_id: str,
    reason: str,
    correction_payload: dict | None = None,
) -> AuditLedger:
    """Append a reverse entry that documents a correction.

    Per Phase 2 spec:
      "nothing in audit_ledger is ever updated or deleted — corrections are
       reverse entries, documented, and permanently visible next to the
       original."

    The original entry is NEVER modified. A new ledger entry is appended
    with action_type='reverse_entry' that references the target by id and
    carries the documented reason.

    Args:
        reason: Required. The human-readable justification for the correction.
        correction_payload: Optional dict with the corrected values.

    Returns:
        The newly appended reverse entry.
    """
    target = (await session.execute(
        select(AuditLedger).where(AuditLedger.id == target_entry_id, AuditLedger.company_id == company_id)
    )).scalar_one_or_none()
    if target is None:
        raise ValueError(f'Reverse target not found: {target_entry_id}')

    payload = {
        'reverse_target_id': target_entry_id,
        'reverse_target_action_type': target.action_type,
        'reverse_target_original_hash': target.action_payload.get('entry_hash'),
        'reason': reason,
        'correction': correction_payload or {},
        'original_unchanged': True,  # explicit guarantee
    }
    return await append_ledger_entry(
        session,
        company_id=company_id,
        actor_user_id=actor_user_id,
        action_type='reverse_entry',
        action_payload=payload,
    )


async def verify_ledger_integrity(session: AsyncSession, company_id, lang: str = 'ar') -> tuple[bool, str, str | None]:
    rows = (await session.execute(select(AuditLedger).where(AuditLedger.company_id == company_id).order_by(AuditLedger.created_at.asc()))).scalars().all()
    previous_hash = 'GENESIS'
    for row in rows:
        body = row.action_payload.get('entry_body', {})
        stored_hash = row.action_payload.get('entry_hash')
        calc = _hash(previous_hash, body)
        if calc != stored_hash:
            return False, tr('ledger.chain_broken', lang).format(entry_id=row.id), str(row.id)
        previous_hash = stored_hash
    return True, tr('ledger.intact', lang), None
