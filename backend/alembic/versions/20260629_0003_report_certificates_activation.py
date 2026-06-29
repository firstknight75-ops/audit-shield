"""Phase 4: Add report_certificate + activation_milestone tables.

Required for:
- Public report verification at /verify/{report_id}
- 48-hour activation tracker with shareable completion banner
- App Owner Clients tab to flag overdue installs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260629_0003'
down_revision = '20260629_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'report_certificate',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('output_code', sa.String(length=100), nullable=False),
        sa.Column('ledger_hash_at_generation', sa.String(length=64), nullable=False),
        sa.Column('signature', sa.String(length=64), nullable=False),
        sa.Column('generated_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('payload_summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_report_certificate_company_id', 'report_certificate', ['company_id'])
    op.create_index('ix_report_certificate_created_at', 'report_certificate', ['created_at'])

    op.create_table(
        'activation_milestone',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage', sa.Integer(), nullable=False),
        sa.Column('stage_key', sa.String(length=100), nullable=False),
        sa.Column('achieved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_activation_milestone_group', 'activation_milestone', ['company_group_id'])
    op.create_index('ix_activation_milestone_stage', 'activation_milestone', ['company_group_id', 'stage'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_activation_milestone_stage', table_name='activation_milestone')
    op.drop_index('ix_activation_milestone_group', table_name='activation_milestone')
    op.drop_table('activation_milestone')
    op.drop_index('ix_report_certificate_created_at', table_name='report_certificate')
    op.drop_index('ix_report_certificate_company_id', table_name='report_certificate')
    op.drop_table('report_certificate')
