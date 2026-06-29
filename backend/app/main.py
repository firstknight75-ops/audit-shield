from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.certification import router as certification_router
from app.api.owner import router as owner_router
from app.api.analytics import router as analytics_router
from app.api.phase4 import router as phase4_router
from app.api.owner_outputs import router as owner_outputs_router
from app.api.trust_proof import router as trust_proof_router
from app.api.layer4 import router as layer4_router
from app.api.silent_ai import router as silent_ai_router
from app.api.verify import router as verify_router
from app.api.activation import router as activation_router
from app.api.inapp import router as inapp_router
from app.api.search import router as search_router
from app.core.config import get_settings
from app.core.middleware import install_security_middleware
from app.core.observability import install_observability

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-seed if needed
    from app.db.session import SessionLocal
    from app.db.seed import seed
    async with SessionLocal() as session:
        await seed(session, deployment_mode=settings.deployment_mode)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    # Disable the default /docs redirect chain — we expose OpenAPI at /openapi.json.
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
)

# Observability must be installed BEFORE security middleware so its
# /health, /ready, /metrics routes are NOT counted against rate limits
# and are NOT stripped of security headers.
install_observability(app)
install_security_middleware(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Translate pydantic validation errors into a stable error envelope."""
    return JSONResponse(
        status_code=422,
        content={
            'detail': 'validation_error',
            'errors': exc.errors(),
            'request_id': getattr(request.state, 'request_id', None),
        },
    )


# Routers
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(documents_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(certification_router, prefix=settings.api_v1_prefix)
app.include_router(owner_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(phase4_router, prefix=settings.api_v1_prefix)
# Principles pass additions
app.include_router(owner_outputs_router, prefix=settings.api_v1_prefix)
app.include_router(trust_proof_router, prefix=settings.api_v1_prefix)
app.include_router(layer4_router, prefix=settings.api_v1_prefix)
app.include_router(silent_ai_router, prefix=settings.api_v1_prefix)
# Phase 4 additions
app.include_router(verify_router)  # /verify/{report_id} — public, no /api prefix
app.include_router(activation_router, prefix=settings.api_v1_prefix)
# Phase 5 additions
app.include_router(inapp_router, prefix=settings.api_v1_prefix)
app.include_router(search_router, prefix=settings.api_v1_prefix)
