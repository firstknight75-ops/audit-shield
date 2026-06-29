"""Silent AI self-test endpoint.

Per AuditCore principle 4: no chatbot, no external AI/LLM API call, ever.
This endpoint proves the guarantee from inside the product.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.services.i18n import tr
from app.services.silent_ai import run_silent_ai_self_test

router = APIRouter(prefix='/silent-ai', tags=['silent-ai'])


@router.get('/self-test')
async def silent_ai_self_test(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the Silent-AI guarantee self-test from inside the product."""
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)

    # Snapshot registered routes for the chatbot-endpoint check
    routes = []
    for r in request.app.routes:
        routes.append({'path': getattr(r, 'path', ''), 'methods': getattr(r, 'methods', [])})

    result = run_silent_ai_self_test(routes=routes)
    return {
        'title': tr('silent_ai.title', lang),
        'subtitle': tr('silent_ai.subtitle', lang),
        'overall_passed': result['overall_passed'],
        'checks': result['checks'],
        'verified_at': datetime.now(timezone.utc).isoformat(),
        'verified_label': tr('silent_ai.verified_now', lang),
    }
