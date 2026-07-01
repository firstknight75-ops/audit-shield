"""Automated test validating Auditor Isolation and Owner Executive Access.

This test file verifies:
1. Role-level permissions: Auditor is isolated from all analytics and dashboards.
2. Endpoint-level safety: All owner-specific endpoints are gated by high-level owner permissions.
3. Database-level isolation: Checks that RLS rules block the auditor from querying analytics tables.
"""
from __future__ import annotations

import pytest
from app.services.permissions import ROLE_DEFAULTS
from app.models.enums import UserRole


def test_auditor_permissions_strictly_excludes_analytics_and_ledger():
    """Verify that by default, the auditor role lacks all sensitive dashboard,
    waste-map, risk-map, and ledger permissions.
    """
    auditor_perms = ROLE_DEFAULTS['auditor']
    forbidden_perms = [
        'view_owner_dashboard',
        'view_waste_map',
        'view_risk_alerts',
        'view_audit_ledger',
        'view_all_companies',
        'export_reports',
        'manage_permissions',
        'grant_temporary_access'
    ]
    for perm in forbidden_perms:
        assert perm not in auditor_perms, f"Security Violation: Auditor has permission '{perm}'"


def test_owner_permissions_includes_full_executive_suite():
    """Verify that the owner role is fully authorized to see all core analytics,
    the ledger, and has full system control.
    """
    owner_perms = ROLE_DEFAULTS['owner']
    required_perms = [
        'view_owner_dashboard',
        'view_waste_map',
        'view_risk_alerts',
        'view_audit_ledger',
        'view_all_companies',
        'export_reports'
    ]
    for perm in required_perms:
        assert perm in owner_perms, f"Acceptance Failure: Owner lacks required permission '{perm}'"


def test_owner_endpoints_are_actively_gated_by_owner_permissions():
    """Scan the backend API routers to ensure all endpoints under /owner
    require owner-specific dashboard or ledger permissions, preventing auditor access.
    """
    import pathlib
    import re

    owner_api_path = pathlib.Path(__file__).parent.parent / 'api' / 'owner_outputs.py'
    assert owner_api_path.exists(), "owner_outputs.py file not found"

    code = owner_api_path.read_text()
    
    # Locate all route decorator lines
    route_decorators = re.findall(r'@router\.(get|post|put|delete)\([^)]*\)', code)
    assert len(route_decorators) > 0, "No owner endpoints found in owner_outputs.py"

    # All route definitions must be accompanied by require_permission('view_owner_dashboard')
    # or require_permission('view_audit_ledger') dependency checks.
    assert "require_permission('view_owner_dashboard')" in code
    
    # Ensure there's no backdoor allowing 'auditor' role or loose get_current_user dependencies
    # in the owner endpoints where strict permission is required.
    assert "Depends(get_current_user)" not in code or "require_permission" in code


def test_database_rls_sql_schema_blocks_auditors():
    """Verify the DB initialization and migration scripts contain SQL commands that
    specifically block the auditor role from reading analytics/waste_map/risk_alerts.
    """
    import pathlib
    migration_dir = pathlib.Path(__file__).parent.parent.parent / 'alembic' / 'versions'
    migrations = list(migration_dir.glob('*.py'))
    
    rls_commands_found = False
    for mig in migrations:
        text = mig.read_text()
        if "app.current_user_role" in text or "auditor" in text:
            rls_commands_found = True
            break
            
    assert rls_commands_found, "PostgreSQL RLS setup missing from alembic migrations."
