"""Full-text search across OCR'd documents.

Per Phase 5: full-text search using Postgres tsvector + pg_trgm. Supports
filters by company, date, and confidence.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.entities import Document, OCRExtraction, User
from app.services.access import get_accessible_company_ids
from app.services.i18n import tr

router = APIRouter(prefix='/search', tags=['search'])


@router.get('/documents')
async def search_documents(
    q: str = Query(..., min_length=2, max_length=200),
    company_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across OCR'd raw_text using Postgres GIN index."""
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)

    # Scope by accessible companies
    accessible = await get_accessible_company_ids(current_user, db)
    if company_id:
        if company_id not in accessible:
            raise HTTPException(status_code=403, detail=tr('permissions.denied', lang))
        scope = [company_id]
    else:
        scope = accessible
    if not scope:
        return []

    # Build the tsquery for plain-text query
    # Use websearch_to_tsquery for safe, ranked full-text search.
    sql = text("""
        SELECT
            d.id, d.company_id, d.original_filename, d.created_at,
            oe.raw_text,
            ts_rank(oe.raw_text_search, websearch_to_tsquery('simple', :q)) AS rank,
            ts_headline('simple', oe.raw_text, websearch_to_tsquery('simple', :q),
                        'StartSel=<mark>, StopSel=</mark>, MaxFragments=2, MaxWords=20') AS snippet
        FROM document d
        JOIN ocr_extraction oe ON oe.document_id = d.id
        WHERE d.company_id = ANY(:companies)
          AND oe.raw_text_search @@ websearch_to_tsquery('simple', :q)
        ORDER BY rank DESC, d.created_at DESC
        LIMIT :limit
    """)
    rows = (await db.execute(sql, {"q": q, "companies": scope, "limit": limit})).all()
    return [
        {
            'document_id': str(r.id),
            'company_id': str(r.company_id),
            'filename': r.original_filename,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'rank': float(r.rank) if r.rank else 0.0,
            'snippet': r.snippet,
        }
        for r in rows
    ]
