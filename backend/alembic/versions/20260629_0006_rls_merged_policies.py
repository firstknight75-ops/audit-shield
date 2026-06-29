"""Phase 1 fix: Merge the two PERMISSIVE RLS policies into one.

Bug #2 (Stabilization pass): In the original 0001_init migration,
each of the three hidden tables had TWO PERMISSIVE policies:

  - auditor_no_access_{table}: USING (current_setting('app.current_user_role', true) != 'auditor')
  - tenant_isolation_{table}:  USING (company_id IN (SELECT ... tenant match))

PostgreSQL combines multiple PERMISSIVE policies for the same command with
**OR**. That meant for any role other than `auditor`, the auditor policy
ALONE evaluated true and the tenant-isolation condition was never checked.
Cross-tenant isolation did not hold for owner/gm/manager/admin/appowner
sessions — even though it was a named Phase 1 acceptance criterion.

This migration drops the two old PERMISSIVE policies and creates a single
PERMISSIVE policy that expresses both conditions with AND directly.
"""
from alembic import op

revision = '20260629_0006'
down_revision = '20260629_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:
        # Drop the two old PERMISSIVE policies
        op.execute(f'DROP POLICY IF EXISTS auditor_no_access_{table} ON {table}')
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}')

        # Create ONE policy with AND — the only correct expression of
        # "block the auditor AND restrict to the current tenant".
        op.execute(
            f"""
            CREATE POLICY access_control_{table} ON {table}
            FOR ALL USING (
                current_setting('app.current_user_role', true) != 'auditor'
                AND company_id IN (
                    SELECT c.id FROM company c
                    JOIN company_group cg ON cg.id = c.company_group_id
                    WHERE cg.id::text = current_setting('app.current_tenant_id', true)
                )
            )
            """
        )


def downgrade() -> None:
    """Restore the original (buggy) policy pair. This is a fix-up migration
    so downgrade preserves the pre-fix behavior for testing comparison.
    """
    for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:
        op.execute(f'DROP POLICY IF EXISTS access_control_{table} ON {table}')
        op.execute(
            f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY'
        )
        op.execute(
            f"CREATE POLICY auditor_no_access_{table} ON {table} "
            f"FOR ALL USING (current_setting('app.current_user_role', true) != 'auditor')"
        )
        op.execute(
            f"CREATE POLICY tenant_isolation_{table} ON {table} "
            f"FOR ALL USING ("
            f"  company_id IN ("
            f"    SELECT c.id FROM company c "
            f"    JOIN company_group cg ON cg.id = c.company_group_id "
            f"    WHERE cg.id::text = current_setting('app.current_tenant_id', true)"
            f"  )"
            f")"
        )
