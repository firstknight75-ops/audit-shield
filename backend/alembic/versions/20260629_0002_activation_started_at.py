"""Phase 1: Add activation_started_at to company_group.

Per AuditCore Phase 1 spec:
  company_group: id, name, tier, deployment_mode, tenant_schema(nullable),
                  activation_started_at(nullable), created_at

`activation_started_at` is stamped by setup.sh / deploy-cloud.sh at the
start of the run — it's the anchor for the Phase 7 (Activation) 48-hour
SLA tracking, and also drives the "first install timestamp" used by
operational dashboards.
"""
from alembic import op
import sqlalchemy as sa

revision = '20260629_0002'
down_revision = '20260629_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'company_group',
        sa.Column('activation_started_at', sa.DateTime(timezone=True), nullable=True),
    )
    # Backfill: existing groups start at created_at so SLA tracking has an
    # anchor from day one of this migration.
    op.execute("UPDATE company_group SET activation_started_at = created_at WHERE activation_started_at IS NULL")


def downgrade() -> None:
    op.drop_column('company_group', 'activation_started_at')
