from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.certification import router as certification_router
from app.api.owner import router as owner_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(documents_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(certification_router, prefix=settings.api_v1_prefix)
app.include_router(owner_router, prefix=settings.api_v1_prefix)


@app.get('/health')
async def health():
    return {'status': 'ok', 'deployment_mode': settings.deployment_mode}
