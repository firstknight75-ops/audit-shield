from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def set_session_context(session: AsyncSession, *, role: str, tenant_schema: str | None = None) -> None:
    await session.execute(text("select set_config('app.current_user_role', :role, true)"), {'role': role})
    if tenant_schema:
        await session.execute(text(f'SET search_path TO {tenant_schema}, public'))
