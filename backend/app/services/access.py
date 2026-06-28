from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Branch, Company, User, UserCompanyAccess
from app.models.enums import UserRole


async def get_accessible_company_ids(user: User, session: AsyncSession) -> list[str]:
    stmt = select(UserCompanyAccess.company_id).where(UserCompanyAccess.user_id == user.id)
    return [str(v) for v in (await session.execute(stmt)).scalars().all()]


async def get_accessible_companies(user: User, session: AsyncSession) -> list[dict]:
    access_rows = (await session.execute(select(UserCompanyAccess).where(UserCompanyAccess.user_id == user.id))).scalars().all()
    by_company: dict[str, dict] = {}
    for row in access_rows:
        company = (await session.execute(select(Company).where(Company.id == row.company_id))).scalars().first()
        if not company:
            continue
        company_key = str(company.id)
        if company_key not in by_company:
            by_company[company_key] = {'company_id': company_key, 'name': company.name, 'branches': []}
        if row.branch_id:
            branch = (await session.execute(select(Branch).where(Branch.id == row.branch_id))).scalars().first()
            if branch:
                by_company[company_key]['branches'].append({'branch_id': str(branch.id), 'name': branch.name})
        else:
            branches = (await session.execute(select(Branch).where(Branch.company_id == company.id))).scalars().all()
            by_company[company_key]['branches'] = [{'branch_id': str(b.id), 'name': b.name} for b in branches]
    return list(by_company.values())


async def require_company_access(user: User, session: AsyncSession, company_id: str, branch_id: str | None = None) -> bool:
    rows = (await session.execute(select(UserCompanyAccess).where(UserCompanyAccess.user_id == user.id, UserCompanyAccess.company_id == company_id))).scalars().all()
    if not rows:
        return False
    if user.role in {UserRole.owner, UserRole.gm, UserRole.admin, UserRole.appowner}:
        return True
    if branch_id is None:
        return True
    return any(row.branch_id is None or str(row.branch_id) == branch_id for row in rows)
