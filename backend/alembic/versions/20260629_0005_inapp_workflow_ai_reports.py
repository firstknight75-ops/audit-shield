"""Phase 5: In-app notifications, workflow events, AI feedback, scheduled reports, quota usage."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260629_0005'
down_revision = '20260629_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'inapp_notification',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('link', sa.String(length=512), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_inapp_user_unread', 'inapp_notification', ['user_id', 'read_at'])
    op.create_index('ix_inapp_user_created', 'inapp_notification', ['user_id', sa.text('created_at DESC')])

    op.create_table(
        'workflow_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workflow', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('payload', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_workflow_company_created', 'workflow_event', ['company_id', sa.text('created_at DESC')])
    op.create_index('ix_workflow_state_due', 'workflow_event', ['state', 'due_at'])

    op.create_table(
        'ai_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('finding_id', sa.String(length=100), nullable=False),
        sa.Column('finding_kind', sa.String(length=50), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('rating', sa.String(length=20), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_ai_feedback_finding', 'ai_feedback', ['finding_id'])

    op.create_table(
        'scheduled_report',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('cron', sa.String(length=100), nullable=False),
        sa.Column('recipients', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_scheduled_report_next', 'scheduled_report', ['next_run_at'], postgresql_where=sa.text('is_active = true'))

    op.create_table(
        'quota_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cap', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('company_group_id', 'metric', 'period_start', name='uq_quota_group_metric_period'),
    )
    op.create_index('ix_quota_usage_group_metric', 'quota_usage', ['company_group_id', 'metric'])


def downgrade() -> None:
    op.drop_index('ix_quota_usage_group_metric', table_name='quota_usage')
    op.drop_table('quota_usage')
    op.drop_index('ix_scheduled_report_next', table_name='scheduled_report')
    op.drop_table('scheduled_report')
    op.drop_index('ix_ai_feedback_finding', table_name='ai_feedback')
    op.drop_table('ai_feedback')
    op.drop_index('ix_workflow_state_due', table_name='workflow_event')
    op.drop_index('ix_workflow_company_created', table_name='workflow_event')
    op.drop_table('workflow_event')
    op.drop_index('ix_inapp_user_created', table_name='inapp_notification')
    op.drop_index('ix_inapp_user_unread', table_name='inapp_notification')
    op.drop_table('inapp_notification')
