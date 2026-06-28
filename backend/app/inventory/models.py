from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClientInventory(Base):
    __tablename__ = 'inventory_client'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    deployment_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    user_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_cap: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    health_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_health_check: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_backup: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dedicated_database_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tenant_schema: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PermissionTemplate(Base):
    __tablename__ = 'inventory_permission_template'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class CraasRequest(Base):
    __tablename__ = 'inventory_craas_request'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending')
    quoted_price_iqd: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deployment_mode: Mapped[str] = mapped_column(String(50), nullable=False)


class AppOwnerAuditEvent(Base):
    __tablename__ = 'inventory_appowner_audit'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_client: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
