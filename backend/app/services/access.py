from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Branch, Company, User, UserCompanyAccess
from app.models.enums import UserRole


async def get_accessible_company_ids(user: User, session: AsyncSession) -> list[str]:
    """Return list of company_id strings the user has explicit access to.

    Every query for documents/tasks/analytics MUST filter through this.
    Default deny: if no user_company_access rows exist, returns [].
    """
    stmt = select(UserCompanyAccess.company_id).where(UserCompanyAccess.user_id == user.id)
    return [str(v) for v in (await session.execute(stmt)).scalars().all()]


async def get_accessible_companies(user: User, session: AsyncSession) -> list[dict]:
    """Return accessible companies with their branches for /auth/me.

    Shape: [{company_id, name, branches: [{branch_id, name}]}]
    If a user has access with branch_id=None, all branches of that company
    are listed. If branch_id is set, only that branch is listed.
    """
    access_rows = (
        await session.execute(select(UserCompanyAccess).where(UserCompanyAccess.user_id == user.id))
    ).scalars().all()

    by_company: dict[str, dict] = {}
    for row in access_rows:
        company = (
            await session.execute(select(Company).where(Company.id == row.company_id))
        ).scalars().first()
        if not company:
            continue
        company_key = str(company.id)
        if company_key not in by_company:
            by_company[company_key] = {'company_id': company_key, 'name': company.name, 'branches': []}

        if row.branch_id is None:
            # Access to all branches of this company
            branches = (
                await session.execute(select(Branch).where(Branch.company_id == company.id))
            ).scalars().all()
            by_company[company_key]['branches'] = [
                {'branch_id': str(b.id), 'name': b.name} for b in branches
            ]
        else:
            # Access to specific branch only
            branch = (
                await session.execute(select(Branch).where(Branch.id == row.branch_id))
            ).scalars().first()
            if branch:
                # Avoid duplicates if multiple access rows point to same branch
                existing_ids = {b['branch_id'] for b in by_company[company_key]['branches']}
                if str(branch.id) not in existing_ids:
                    by_company[company_key]['branches'].append({
                        'branch_id': str(branch.id),
                        'name': branch.name,
                    })

    return list(by_company.values())


async def require_company_access(
    user: User,
    session: AsyncSession,
    company_id: str,
    branch_id: str | None = None,
) -> bool:
    """Check whether a user has access to the given company (and optionally branch).

    Returns True if access is granted, False otherwise.
    Default deny: no user_company_access row means no access.

    Rules:
    - owner/gm/admin/appowner: granted if any access row exists for this company
    - manager/auditor: must have matching company_id AND matching branch_id
      (or branch_id=None in access row means all branches)
    """
    rows = (
        await session.execute(
            select(UserCompanyAccess).where(
                UserCompanyAccess.user_id == user.id,
                UserCompanyAccess.company_id == company_id,
            )
        )
    ).scalars().all()

    if not rows:
        return False

    # Owner, GM, Admin, AppOwner: broad access within the company
    if user.role in {UserRole.owner, UserRole.gm, UserRole.admin, UserRole.appowner}:
        return True

    # Manager, Auditor: check branch-level access
    if branch_id is None:
        # No specific branch requested — company-level access is sufficient
        return True

    # Check if any access row covers the requested branch
    return any(
        row.branch_id is None or str(row.branch_id) == branch_id
        for row in rows
    )


async def get_accessible_branch_ids(
    user: User,
    session: AsyncSession,
    company_id: str,
) -> list[str]:
    """Return list of branch_id strings the user can access within a company.

    Returns [] if user has no company access, or all branch IDs if user has all-branch access.
    """
    rows = (
        await session.execute(
            select(UserCompanyAccess).where(
                UserCompanyAccess.user_id == user.id,
                UserCompanyAccess.company_id == company_id,
            )
        )
    ).scalars().all()

    if not rows:
        return []

    # If any row has branch_id=None, user has all-branch access
    if any(row.branch_id is None for row in rows):
        all_branches = (
            await session.execute(select(Branch).where(Branch.company_id == company_id))
        ).scalars().all()
        return [str(b.id) for b in all_branches]

    return [str(row.branch_id) for row in rows if row.branch_id]
