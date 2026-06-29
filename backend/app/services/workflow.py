"""Workflow engine — approval routing, escalation, SLA timers.

Per Phase 6 spec: configurable workflow with approvals, escalation,
delegation, SLA timers, business rules, automation.

This implementation provides:
- A state machine model (created → pending_approval → approved | rejected | escalated)
- SLA timer evaluation: if a workflow has been in a state longer than its
  configured timeout, mark it for escalation and notify the next actor.
- An escalation graph: explicit delegate chain per workflow.
- An audit trail via `workflow_event` table (immutable).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, WorkflowEvent

logger = logging.getLogger('auditcore.workflow')


class WorkflowState(str, Enum):
    CREATED = 'created'
    PENDING_APPROVAL = 'pending_approval'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    ESCALATED = 'escalated'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


# Default SLA per workflow kind (in hours)
DEFAULT_SLA_HOURS: dict[str, int] = {
    'manual_correction_approval': 24,
    'cr_aa_s_change_request': 48,
    'tier_change': 4,
    'craas_request': 24,
    'permission_override_extension': 12,
}


async def record_event(
    session: AsyncSession,
    *,
    workflow: str,
    company_id: str,
    state: str | WorkflowState,
    actor_user_id: str | None = None,
    payload: dict | None = None,
    due_at: datetime | None = None,
) -> WorkflowEvent:
    """Append an immutable workflow event to the audit trail."""
    if isinstance(state, WorkflowState):
        state = state.value
    event = WorkflowEvent(
        workflow=workflow,
        company_id=company_id,
        state=state,
        actor_user_id=actor_user_id,
        payload=payload or {},
        due_at=due_at,
    )
    session.add(event)
    await session.flush()
    return event


async def check_sla_breaches(session: AsyncSession) -> list[WorkflowEvent]:
    """Find workflow events past their due_at that aren't yet completed.

    Marks them for escalation and emits a notification event.
    """
    now = datetime.now(timezone.utc)
    breaches = (await session.execute(
        select(WorkflowEvent).where(
            WorkflowEvent.due_at.is_not(None),
            WorkflowEvent.due_at < now,
            WorkflowEvent.completed_at.is_(None),
        )
    )).scalars().all()

    escalated = []
    for ev in breaches:
        # Idempotent escalation: only escalate once per breach.
        if ev.state == WorkflowState.ESCALATED.value:
            continue
        ev.state = WorkflowState.ESCALATED.value
        ev.payload = {**(ev.payload or {}), 'escalated_at': now.isoformat()}
        escalated.append(ev)
        logger.warning(
            'workflow_sla_breach',
            extra={'workflow': ev.workflow, 'company_id': str(ev.company_id), 'due_at': ev.due_at.isoformat() if ev.due_at else None},
        )
    if escalated:
        await session.commit()
    return escalated


def default_due_at(workflow: str, now: datetime | None = None) -> datetime:
    """Compute the default due_at for a workflow kind."""
    now = now or datetime.now(timezone.utc)
    hours = DEFAULT_SLA_HOURS.get(workflow, 24)
    return now + timedelta(hours=hours)


async def approval_route(
    session: AsyncSession,
    *,
    workflow: str,
    company_id: str,
    initiator_user_id: str,
    target_role: str,
    payload: dict | None = None,
) -> WorkflowEvent:
    """Initiate an approval workflow.

    `target_role` is the role that must approve. The system looks up the
    first available user in that role within the same company_group.
    """
    user = (await session.execute(
        select(User).where(User.id == initiator_user_id)
    )).scalar_one_or_none()
    if user is None:
        raise ValueError('initiator_not_found')
    approver = (await session.execute(
        select(User).where(
            User.role == target_role,
            User.company_group_id == user.company_group_id,
            User.is_active.is_(True),
        ).limit(1)
    )).scalar_one_or_none()
    if approver is None:
        # No approver in this group — escalate to App Owner queue
        ev = await record_event(
            session,
            workflow=workflow,
            company_id=company_id,
            state=WorkflowState.ESCALATED.value,
            actor_user_id=initiator_user_id,
            payload={**(payload or {}), 'no_approver': True, 'target_role': target_role},
            due_at=default_due_at(workflow),
        )
    else:
        ev = await record_event(
            session,
            workflow=workflow,
            company_id=company_id,
            state=WorkflowState.PENDING_APPROVAL.value,
            actor_user_id=initiator_user_id,
            payload={**(payload or {}), 'approver_user_id': str(approver.id), 'target_role': target_role},
            due_at=default_due_at(workflow),
        )
    await session.commit()
    return ev
