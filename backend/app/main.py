from contextlib import asynccontextmanager

from fastapi import FastAPI

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
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-seed if needed
    from app.db.session import SessionLocal
    from app.db.seed import seed
    async with SessionLocal() as session:
        await seed(session, deployment_mode=settings.deployment_mode)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
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


@app.get('/health')
async def health():
    return {'status': 'ok', 'deployment_mode': settings.deployment_mode}
