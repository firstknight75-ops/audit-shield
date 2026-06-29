"""Phase 5: Production indexes + full-text search support.

Adds:
- Composite indexes for the high-traffic queries (company-scoped reads, recent-by-company)
- Indexes on (company_id, created_at) for time-ordered listings
- Indexes on FK columns that the audit and dashboard queries depend on
- GIN indexes on raw_text for full-text search (pg_trgm + tsvector)
"""
from alembic import op
import sqlalchemy as sa

revision = '20260629_0004'
down_revision = '20260629_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Audit ledger ────────────────────────────────────────────────
    # Most queries: list entries for a company, newest first.
    op.create_index('ix_audit_ledger_company_created', 'audit_ledger', ['company_id', sa.text('created_at DESC')])
    op.create_index('ix_audit_ledger_action_type', 'audit_ledger', ['action_type'])

    # ── Document + OCR ──────────────────────────────────────────────
    op.create_index('ix_document_company_created', 'document', ['company_id', sa.text('created_at DESC')])
    op.create_index('ix_document_company_branch', 'document', ['company_id', 'branch_id'])
    op.create_index('ix_ocr_extraction_certified_at', 'ocr_extraction', ['certified_at'])

    # ── Daily tasks ─────────────────────────────────────────────────
    # Heavy query: "open tasks for an auditor in their company, due soonest first"
    op.create_index('ix_daily_task_auditor_status_due', 'daily_task', ['auditor_user_id', 'status', 'due_at'])
    op.create_index('ix_daily_task_company_status', 'daily_task', ['company_id', 'status'])

    # ── Analytics + waste + risk ───────────────────────────────────
    op.create_index('ix_analytics_output_company_created', 'analytics_outputs', ['company_id', sa.text('created_at DESC')])
    op.create_index('ix_waste_map_item_company_category', 'waste_map_items', ['company_id', 'category'])
    op.create_index('ix_risk_alert_company_status', 'risk_alerts', ['company_id', 'status', 'severity'])

    # ── User / access control ──────────────────────────────────────
    op.create_index('ix_user_company_access_company', 'user_company_access', ['company_id'])
    op.create_index('ix_user_company_access_user', 'user_company_access', ['user_id'])

    # ── Permissions ───────────────────────────────────────────────
    op.create_index('ix_user_permission_override_user_active', 'user_permission_override', ['user_id', 'is_active'])

    # ── Activation milestones + report certificates ──────────────
    op.create_index('ix_activation_milestone_group_achieved', 'activation_milestone', ['company_group_id', 'achieved_at'])
    op.create_index('ix_report_certificate_company_created', 'report_certificate', ['company_id', sa.text('created_at DESC')])

    # ── Inventory (App Owner) ──────────────────────────────────────
    # App Owner dashboard list: clients per tenant (rare query — not heavily indexed)

    # ── Full-text search on raw OCR text ────────────────────────────
    # Use GIN index on raw_text for ILIKE / similarity searches.
    # We use a generated tsvector column; requires postgres >= 12.
    op.execute("""
        ALTER TABLE ocr_extraction
        ADD COLUMN IF NOT EXISTS raw_text_search tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple', coalesce(raw_text, ''))
        ) STORED
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ocr_raw_text_search ON ocr_extraction USING GIN (raw_text_search)")

    # Same for document.metadata_json's invoice_number-ish fields (varchar only)
    op.create_index('ix_document_metadata_invoice_gin', 'document', ['metadata_json'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ix_document_metadata_invoice_gin', table_name='document')
    op.execute("DROP INDEX IF EXISTS ix_ocr_raw_text_search")
    op.execute("ALTER TABLE ocr_extraction DROP COLUMN IF EXISTS raw_text_search")
    op.drop_index('ix_report_certificate_company_created', table_name='report_certificate')
    op.drop_index('ix_activation_milestone_group_achieved', table_name='activation_milestone')
    op.drop_index('ix_user_permission_override_user_active', table_name='user_permission_override')
    op.drop_index('ix_user_company_access_user', table_name='user_company_access')
    op.drop_index('ix_user_company_access_company', table_name='user_company_access')
    op.drop_index('ix_risk_alert_company_status', table_name='risk_alerts')
    op.drop_index('ix_waste_map_item_company_category', table_name='waste_map_items')
    op.drop_index('ix_analytics_output_company_created', table_name='analytics_outputs')
    op.drop_index('ix_daily_task_company_status', table_name='daily_task')
    op.drop_index('ix_daily_task_auditor_status_due', table_name='daily_task')
    op.drop_index('ix_ocr_extraction_certified_at', table_name='ocr_extraction')
    op.drop_index('ix_document_company_branch', table_name='document')
    op.drop_index('ix_document_company_created', table_name='document')
    op.drop_index('ix_audit_ledger_action_type', table_name='audit_ledger')
    op.drop_index('ix_audit_ledger_company_created', table_name='audit_ledger')
