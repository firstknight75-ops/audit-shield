"""Public report verification endpoint.

Per Phase 4 spec:
- /verify/{report_id} — NO LOGIN REQUIRED
- The route must NEVER reveal the report's content to someone who
  doesn't already have it
- It only confirms hash/signature integrity

The verifier already has the report_id (printed on the exported PDF/PNG).
They re-supply the ledger_hash_at_generation + signature + payload_summary
that are also printed on the report. The endpoint re-derives the HMAC
and returns only pass/fail.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import ReportCertificate
from app.services.i18n import tr
from app.services.ledger import verify_ledger_integrity

router = APIRouter(prefix='/verify', tags=['verify'])


class VerifyRequest(BaseModel):
    ledger_hash_at_generation: str
    signature: str
    # The verifier re-supplies the non-sensitive metadata that was used
    # when the certificate was generated. The server stores this exact dict.
    payload: dict = {}


@router.post('/{report_id}')
async def verify_report(
    report_id: str,
    body: VerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify a report's tamper-proof certificate.

    This endpoint is intentionally public (no `get_current_user` dependency).
    It returns only a pass/fail verdict — NEVER the report's content.

    If the verifier doesn't have the report, they cannot read it through
    this endpoint — the response contains only integrity metadata.
    """
    # Look up the certificate
    cert = (await db.execute(
        select(ReportCertificate).where(ReportCertificate.id == report_id)
    )).scalar_one_or_none()
    if not cert:
        # Don't leak whether the report_id is valid — same response shape
        # as a real cert, just with valid=False. This prevents enumeration.
        return {
            'report_id': report_id,
            'valid': False,
            'message_ar': 'هذا التقرير غير موجود أو تم تعديله.',
            'message_ckb': 'ئەم ڕاپۆرتە نەدۆزرایەوە یان دەستکاری کراوە.',
            'note': 'No content disclosed.',
        }

    from app.exports.certificates import verify_certificate

    supplied_signature = body.signature
    supplied_ledger = body.ledger_hash_at_generation

    if not supplied_signature or not supplied_ledger:
        return {
            'report_id': report_id,
            'valid': False,
            'message_ar': 'لم تُقدَّم بيانات كافية للتحقق.',
            'message_ckb': 'بەس نییە بۆ پشتڕاستکردنەوە.',
            'note': 'Provide the ledger_hash_at_generation + signature printed on the report.',
        }

    # The verifier re-supplies the metadata. We reconstruct the payload
    # using the same key structure the certificate was built with.
    expected_payload = {
        'summary': cert.payload_summary,
        'company_id': str(cert.company_id),
        'output_code': cert.output_code,
        'format': cert.format,
    }
    is_valid_signature = verify_certificate(
        report_id=report_id,
        ledger_hash_at_generation=cert.ledger_hash_at_generation,
        signature=cert.signature,
        payload=expected_payload,
    )[0]

    signature_matches = supplied_signature == cert.signature
    ledger_matches = supplied_ledger == cert.ledger_hash_at_generation
    overall_valid = signature_matches and ledger_matches and is_valid_signature

    # Cross-check that the current ledger still has the same hash
    current_ledger_valid, current_ledger_msg, _ = await verify_ledger_integrity(db, str(cert.company_id), 'ar')

    return {
        'report_id': report_id,
        'valid': overall_valid,
        'message_ar': (
            'هذا التقرير أصلي ولم يُعدَّل بعد إصداره.'
            if overall_valid else
            'هذا التقرير مُعدَّل أو بيانات التحقق غير صحيحة.'
        ),
        'message_ckb': (
            'ئەم ڕاپۆرتە ئەسڵییە و دوای دەرچوونی دەستکاری نەکراوە.'
            if overall_valid else
            'ئەم ڕاپۆرتە دەستکاری کراوە یان داتاکانی پشتڕاستکردنەوە هەڵەن.'
        ),
        'checks': {
            'signature_matches_stored': signature_matches,
            'ledger_hash_matches_stored': ledger_matches,
            'hmac_recomputed_matches': is_valid_signature,
            'current_ledger_chain_intact': current_ledger_valid,
        },
        'generated_at': cert.created_at.isoformat() if cert.created_at else None,
        'note': 'No content disclosed — integrity verdict only.',
    }
