#!/usr/bin/env bash
set -euo pipefail
TENANT_NAME="${1:-tenant-demo}"
TENANT_TIER="${2:-essential}"
TENANT_SCHEMA="${3:-tenant_${RANDOM}}"
cd "$(dirname "$0")/.."
export DEPLOYMENT_MODE=cloud
docker compose up -d postgres redis
sleep 5
docker compose build backend
docker compose up -d backend celery-worker celery-beat
cat <<PY | docker compose exec -T backend python
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from alembic.config import Config
from alembic import command
from app.core.config import get_settings
from app.db.seed import seed

settings = get_settings()
command.upgrade(Config('alembic.ini'), 'head')
engine = create_async_engine(settings.database_url)
Session = async_sessionmaker(engine, expire_on_commit=False)
async def main():
    async with engine.begin() as conn:
        if '${TENANT_TIER}' != 'elite':
            await conn.execute(text('CREATE SCHEMA IF NOT EXISTS ${TENANT_SCHEMA}'))
    async with Session() as session:
        if '${TENANT_TIER}' != 'elite':
            await session.execute(text('SET search_path TO ${TENANT_SCHEMA}, public'))
        await seed(session, deployment_mode='cloud', company_name='${TENANT_NAME}', tenant_schema='${TENANT_SCHEMA}' if '${TENANT_TIER}' != 'elite' else None)
asyncio.run(main())
PY
printf '\nSeeded credentials:\n'
printf 'owner@auditcore.local / Owner123!\n'
printf 'gm@auditcore.local / Gm123!\n'
printf 'manager@auditcore.local / Manager123!\n'
printf 'auditor@auditcore.local / Auditor123!\n'
printf 'sysadmin@auditcore.local / Sysadmin123!\n'
printf 'appowner@auditcore.local / Appowner123!\n'
printf '\nInventory registration and Vault secret scaffolding assumed in this phase scaffold.\n'
