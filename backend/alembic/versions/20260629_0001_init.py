"""AuditCore foundation — company_group hierarchy, bilingual, RLS

This migration replaces the old 20260628_0001_init schema with the
new multi-company hierarchy and bilingual foundation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260629_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enum types ──────────────────────────────────────────────
    company_group_tier = sa.Enum('essential', 'advanced', 'elite', name='company_group_tier')
    group_deployment_mode = sa.Enum('onpremise', 'cloud', name='group_deployment_mode')
    user_role = sa.Enum('owner', 'gm', 'manager', 'auditor', 'admin', 'appowner', name='user_role')
    preferred_language = sa.Enum('ar', 'ckb', name='preferred_language')
    role_permission_role = sa.Enum('owner', 'gm', 'manager', 'auditor', 'admin', 'appowner', name='role_permission_role')
    override_action = sa.Enum('grant', 'revoke', name='override_action')
    translation_language = sa.Enum('ar', 'ckb', name='translation_language')

    company_group_tier.create(op.get_bind(), checkfirst=True)
    group_deployment_mode.create(op.get_bind(), checkfirst=True)
    user_role.create(op.get_bind(), checkfirst=True)
    preferred_language.create(op.get_bind(), checkfirst=True)
    role_permission_role.create(op.get_bind(), checkfirst=True)
    override_action.create(op.get_bind(), checkfirst=True)
    translation_language.create(op.get_bind(), checkfirst=True)

    op.execute('CREATE SCHEMA IF NOT EXISTS inventory')

    # ── company_group (tenant boundary) ─────────────────────────
    op.create_table(
        'company_group',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tier', company_group_tier, nullable=False),
        sa.Column('deployment_mode', group_deployment_mode, nullable=False),
        sa.Column('tenant_schema', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── company ─────────────────────────────────────────────────
    op.create_table(
        'company',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── branch ──────────────────────────────────────────────────
    op.create_table(
        'branch',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── user_account ────────────────────────────────────────────
    op.create_table(
        'user_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', user_role, nullable=False),
        sa.Column('company_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('preferred_language', preferred_language, nullable=False, server_default='ar'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── user_company_access ─────────────────────────────────────
    op.create_table(
        'user_company_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── document ────────────────────────────────────────────────
    op.create_table(
        'document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('uploaded_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('encrypted_blob', sa.LargeBinary(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── audit_task ──────────────────────────────────────────────
    op.create_table(
        'audit_task',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── document_certification ──────────────────────────────────
    op.create_table(
        'document_certification',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document.id', ondelete='CASCADE'), nullable=False),
        sa.Column('certified_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('certification_status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── audit_ledger ────────────────────────────────────────────
    op.create_table(
        'audit_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── analytics_outputs (hidden from auditor via RLS) ─────────
    op.create_table(
        'analytics_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('output_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── waste_map_items (hidden from auditor via RLS) ───────────
    op.create_table(
        'waste_map_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('iqd_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── risk_alerts (hidden from auditor via RLS) ───────────────
    op.create_table(
        'risk_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── permission ──────────────────────────────────────────────
    op.create_table(
        'permission',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=100), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )

    # ── role_permission ─────────────────────────────────────────
    op.create_table(
        'role_permission',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role', role_permission_role, nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permission.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
    )

    # ── user_permission_override ────────────────────────────────
    op.create_table(
        'user_permission_override',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permission.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=True),
        sa.Column('action', override_action, nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── translation ─────────────────────────────────────────────
    op.create_table(
        'translation',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('language', translation_language, nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.UniqueConstraint('key', 'language', name='uq_translation_key_language'),
    )

    # ── ocr_extraction ──────────────────────────────────────────
    op.create_table(
        'ocr_extraction',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('extracted_data', sa.JSON(), nullable=False),
        sa.Column('confidence_map', sa.JSON(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('certified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('certified_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='SET NULL')),
    )

    # ── daily_task ──────────────────────────────────────────────
    op.create_table(
        'daily_task',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=False),
        sa.Column('auditor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document.id', ondelete='SET NULL')),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sla_minutes', sa.Integer(), nullable=False),
        sa.Column('demerit_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── notification_queue ──────────────────────────────────────
    op.create_table(
        'notification_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company.id', ondelete='CASCADE'), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # ── inventory schema tables (app-owner platform) ────────────
    op.create_table(
        'inventory_client',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('deployment_mode', sa.String(length=50), nullable=False),
        sa.Column('user_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('user_cap', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('health_url', sa.String(length=255), nullable=True),
        sa.Column('last_health_check', sa.String(length=255), nullable=True),
        sa.Column('last_backup', sa.String(length=255), nullable=True),
        sa.Column('dedicated_database_url', sa.Text(), nullable=True),
        sa.Column('tenant_schema', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='inventory',
    )

    op.create_table(
        'inventory_permission_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('payload_json', sa.Text(), nullable=False),
        schema='inventory',
    )

    op.create_table(
        'inventory_craas_request',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('quoted_price_iqd', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deployment_mode', sa.String(length=50), nullable=False),
        schema='inventory',
    )

    op.create_table(
        'inventory_appowner_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('target_client', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='inventory',
    )

    # ── RLS: auditor-denied tables ──────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_user_role(role text) RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_user_role', role, true);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Auditor must NEVER see analytics_outputs, waste_map_items, risk_alerts
    for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"CREATE POLICY auditor_no_access_{table} ON {table} "
            f"FOR ALL USING (current_setting('app.current_user_role', true) != 'auditor')"
        )

    # Additionally enforce tenant isolation on these hidden tables
    # so even an owner/gm of one company_group cannot read another's hidden data
    for table in ['analytics_outputs', 'waste_map_items', 'risk_alerts']:
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


def downgrade() -> None:
    pass
