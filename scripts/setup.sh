#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d postgres redis
sleep 5
docker compose build backend
docker compose up -d backend baileys-bridge
cat <<'PY' | docker compose exec -T backend python
import asyncio
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
    async with Session() as session:
        await seed(session, deployment_mode='onpremise')
asyncio.run(main())
PY
printf '\nSeeded credentials:\n'
printf 'owner@auditcore.local / Owner123!\n'
printf 'gm@auditcore.local / Gm123!\n'
printf 'manager@auditcore.local / Manager123!\n'
printf 'auditor@auditcore.local / Auditor123!\n'
printf 'sysadmin@auditcore.local / Sysadmin123!\n'
printf 'appowner@auditcore.local / Appowner123!\n'
