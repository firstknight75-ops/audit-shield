from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CompanyTier, DeploymentMode, OverrideAction, PreferredLanguage, UserRole


class CompanyGroup(Base):
    __tablename__ = 'company_group'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[CompanyTier] = mapped_column(Enum(CompanyTier, name='company_group_tier'), nullable=False)
    deployment_mode: Mapped[DeploymentMode] = mapped_column(Enum(DeploymentMode, name='group_deployment_mode'), nullable=False)
    tenant_schema: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Company(Base):
    __tablename__ = 'company'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Branch(Base):
    __tablename__ = 'branch'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = 'user_account'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name='user_role'), nullable=False)
    company_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_language: Mapped[PreferredLanguage] = mapped_column(Enum(PreferredLanguage, name='preferred_language'), nullable=False, default=PreferredLanguage.ar)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserCompanyAccess(Base):
    __tablename__ = 'user_company_access'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('branch.id', ondelete='SET NULL'), nullable=True)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Document(Base):
    __tablename__ = 'document'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('branch.id', ondelete='SET NULL'))
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    encrypted_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditTask(Base):
    __tablename__ = 'audit_task'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('branch.id', ondelete='SET NULL'))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='open', nullable=False)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DocumentCertification(Base):
    __tablename__ = 'document_certification'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('document.id', ondelete='CASCADE'), nullable=False)
    certified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))
    certification_status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLedger(Base):
    __tablename__ = 'audit_ledger'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AnalyticsOutput(Base):
    __tablename__ = 'analytics_outputs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('branch.id', ondelete='SET NULL'))
    output_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WasteMapItem(Base):
    __tablename__ = 'waste_map_items'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('branch.id', ondelete='SET NULL'))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    iqd_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RiskAlert(Base):
    __tablename__ = 'risk_alerts'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('branch.id', ondelete='SET NULL'))
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='open', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Permission(Base):
    __tablename__ = 'permission'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class RolePermission(Base):
    __tablename__ = 'role_permission'
    __table_args__ = (UniqueConstraint('role', 'permission_id', name='uq_role_permission'),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name='role_permission_role'), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('permission.id', ondelete='CASCADE'), nullable=False)


class UserPermissionOverride(Base):
    __tablename__ = 'user_permission_override'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('permission.id', ondelete='CASCADE'), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=True)
    action: Mapped[OverrideAction] = mapped_column(Enum(OverrideAction, name='override_action'), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Translation(Base):
    __tablename__ = 'translation'
    __table_args__ = (UniqueConstraint('key', 'language', name='uq_translation_key_language'),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[PreferredLanguage] = mapped_column(Enum(PreferredLanguage, name='translation_language'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class OCRExtraction(Base):
    __tablename__ = 'ocr_extraction'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('document.id', ondelete='CASCADE'), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    extracted_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence_map: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    certified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    certified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))


class DailyTask(Base):
    __tablename__ = 'daily_task'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    auditor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='open', nullable=False)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('document.id', ondelete='SET NULL'))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    demerit_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default='normal', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NotificationQueue(Base):
    __tablename__ = 'notification_queue'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default='low')
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='queued')
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReportCertificate(Base):
    """Tamper-Proof Certificate for an exported report.

    Stored server-side so /verify/{report_id} can re-validate the HMAC
    signature without revealing the report's content to the verifier.
    Per Phase 4: the verifier never sees the report's data — only confirms
    hash/signature integrity.
    """
    __tablename__ = 'report_certificate'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    output_code: Mapped[str] = mapped_column(String(100), nullable=False)
    ledger_hash_at_generation: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('user_account.id', ondelete='SET NULL'))
    payload_summary: Mapped[str] = mapped_column(Text, nullable=False)  # non-sensitive metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ActivationMilestone(Base):
    """Per-company_group 48-hour activation milestones (Phase 4).

    Records each of the four stages so the Owner can see progress and
    a shareable completion banner appears at stage 4.
    """
    __tablename__ = 'activation_milestone'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('company_group.id', ondelete='CASCADE'), nullable=False)
    stage: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..4
    stage_key: Mapped[str] = mapped_column(String(100), nullable=False)
    achieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
