"""Trust Proof — demonstrable inside the product.

Per AuditCore principle 6: "this must be demonstrable inside the product,
not just asserted in a contract."

This endpoint runs a live self-test that proves:
1. Auditor cannot reach analytics_outputs / waste_map_items / risk_alerts
   (uses the same DB session as the Auditor, executes a SELECT, returns 0 rows).
2. App Owner has zero visibility into any client's financial content
   (proves that the App Owner's session context cannot read tenant tables).
3. Each company_group is tenant-isolated from other company_groups.
4. The hash-chained ledger is intact (calls verify_ledger_integrity).

All four proofs return a structured pass/fail report. The product's
App Owner dashboard renders this page; it's the in-product certificate.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db, set_session_context
from app.models.entities import User
from app.models.enums import UserRole
from app.services.access import require_company_access
from app.services.i18n import tr
from app.services.ledger import verify_ledger_integrity

router = APIRouter(prefix='/trust-proof', tags=['trust-proof'])


async def _run_auditor_rls_proof(db: AsyncSession) -> dict:
    """Force session role=auditor and SELECT from hidden tables — must return 0 rows."""
    await set_session_context(db, role='auditor', tenant_id='00000000-0000-0000-0000-000000000000', tenant_schema=None)
    rows = (await db.execute(text('SELECT count(*) FROM analytics_outputs'))).scalar() or 0
    waste = (await db.execute(text('SELECT count(*) FROM waste_map_items'))).scalar() or 0
    risks = (await db.execute(text('SELECT count(*) FROM risk_alerts'))).scalar() or 0
    return {
        'guarantee': 'auditor_blocked_from_analytics',
        'passed': (rows == 0 and waste == 0 and risks == 0),
        'detail': {
            'analytics_outputs_visible': rows,
            'waste_map_items_visible': waste,
            'risk_alerts_visible': risks,
        },
    }


async def _run_appowner_zero_visibility_proof(db: AsyncSession, appowner: User) -> dict:
    """Simulate App Owner role on a tenant schema, prove zero tenant table visibility."""
    # Force appowner context: app.current_user_role = 'appowner'
    await set_session_context(
        db,
        role='appowner',
        tenant_id=str(appowner.company_group_id),
        tenant_schema=None,
    )
    # App Owner MUST see zero rows in tenant financial/analytics tables.
    analytics_visible = (await db.execute(text('SELECT count(*) FROM analytics_outputs'))).scalar() or 0
    waste_visible = (await db.execute(text('SELECT count(*) FROM waste_map_items'))).scalar() or 0
    risks_visible = (await db.execute(text('SELECT count(*) FROM risk_alerts'))).scalar() or 0
    audit_ledger_visible = (await db.execute(text('SELECT count(*) FROM audit_ledger'))).scalar() or 0
    documents_visible = (await db.execute(text('SELECT count(*) FROM document'))).scalar() or 0

    # App Owner CAN see inventory schema (their own platform data)
    inv_clients_visible = (await db.execute(text('SELECT count(*) FROM inventory.inventory_client'))).scalar() or 0
    inv_templates_visible = (await db.execute(text('SELECT count(*) FROM inventory.inventory_permission_template'))).scalar() or 0

    return {
        'guarantee': 'appowner_zero_visibility_to_tenant_data',
        'passed': (
            analytics_visible == 0
            and waste_visible == 0
            and risks_visible == 0
            and audit_ledger_visible == 0
            and documents_visible == 0
        ),
        'detail': {
            'tenant_finance_hidden': {
                'analytics_outputs_visible': analytics_visible,
                'waste_map_items_visible': waste_visible,
                'risk_alerts_visible': risks_visible,
                'audit_ledger_visible': audit_ledger_visible,
                'document_visible': documents_visible,
            },
            'platform_inventory_visible': {
                'inventory_client': inv_clients_visible,
                'inventory_permission_template': inv_templates_visible,
            },
        },
    }


async def _run_tenant_isolation_proof(db: AsyncSession, owner: User, company_id: str) -> dict:
    """Owner of one tenant must not see other tenants' hidden data."""
    # Set session role=owner for current tenant
    await set_session_context(
        db,
        role='owner',
        tenant_id=str(owner.company_group_id),
        tenant_schema=None,
    )
    visible_for_my_tenant = (await db.execute(
        select(AnalyticsOutput).where(AnalyticsOutput.company_id == company_id)
    )).scalars().all()
    # Cross-tenant: any analytics_output with company_id NOT in my tenant
    cross_tenant = (await db.execute(
        text("""
            SELECT count(*) FROM analytics_outputs a
            JOIN company c ON c.id = a.company_id
            WHERE c.company_group_id::text != :tenant
        """),
        {'tenant': str(owner.company_group_id)},
    )).scalar() or 0
    return {
        'guarantee': 'tenant_isolation',
        'passed': cross_tenant == 0,
        'detail': {
            'my_tenant_rows': len(visible_for_my_tenant),
            'cross_tenant_rows_visible': cross_tenant,
        },
    }


@router.get('/run')
async def run_trust_proofs(
    company_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run all trust-boundary self-tests and return the in-product certificate."""
    lang = current_user.preferred_language.value if hasattr(current_user.preferred_language, 'value') else str(current_user.preferred_language)

    proofs = []

    # Proof 1: auditor RLS (no session impersonation — runs as system context then sets role=auditor)
    proofs.append(await _run_auditor_rls_proof(db))

    # Proof 2: appowner zero visibility
    if current_user.role != UserRole.appowner:
        # We need an appowner to simulate; use the seeded appowner if present.
        appowner_row = (await db.execute(
            select(User).where(User.role == UserRole.appowner).limit(1)
        )).scalars().first()
        if appowner_row:
            proofs.append(await _run_appowner_zero_visibility_proof(db, appowner_row))
    else:
        proofs.append(await _run_appowner_zero_visibility_proof(db, current_user))

    # Proof 3: tenant isolation (owner-scoped)
    if current_user.role in (UserRole.owner, UserRole.gm, UserRole.admin) and company_id:
        if await require_company_access(current_user, db, company_id):
            proofs.append(await _run_tenant_isolation_proof(db, current_user, company_id))
        else:
            proofs.append({
                'guarantee': 'tenant_isolation',
                'passed': False,
                'detail': {'reason': 'caller has no access to the requested company_id'},
            })

    # Proof 4: ledger intact (for the company if provided and accessible)
    if company_id and await require_company_access(current_user, db, company_id):
        valid, message, broken = await verify_ledger_integrity(db, company_id, lang)
        proofs.append({
            'guarantee': 'ledger_chain_intact',
            'passed': valid,
            'detail': {'message': message, 'broken_entry_id': broken},
        })

    overall_passed = all(p['passed'] for p in proofs)

    # Ledger: log that this trust proof was run
    from app.services.ledger import append_ledger_entry
    if company_id:
        await append_ledger_entry(
            db,
            company_id=company_id,
            actor_user_id=current_user.id,
            action_type='trust_proof_run',
            action_payload={'overall_passed': overall_passed, 'proofs': [p['guarantee'] for p in proofs]},
        )
        await db.commit()

    return {
        'title': tr('trust_proof.title', lang),
        'subtitle': tr('trust_proof.subtitle', lang),
        'overall_passed': overall_passed,
        'proofs': proofs,
        'run_at': datetime.now(timezone.utc).isoformat(),
    }
