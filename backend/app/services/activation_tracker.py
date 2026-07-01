"""48-Hour Activation Tracker (Phase 4).

Four stages, each timestamped:
  1. تثبيت الجهاز/الحساب — device/account provisioned
  2. تهيئة المستخدمين — users created
  3. أول دفعة مستندات — first document batch
  4. أول تحليل وتقرير — first analysis & report

If stage 4 is reached within 48 hours, a shareable completion banner
appears. Otherwise the install is flagged in the App Owner Clients tab.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ActivationMilestone, AnalyticsOutput, Company, CompanyGroup, Document


STAGES = [
    (1, 'device_provisioned', 'تثبيت الجهاز/الحساب'),
    (2, 'users_initialized', 'تهيئة المستخدمين'),
    (3, 'first_document_batch', 'أول دفعة مستندات'),
    (4, 'first_analysis_report', 'أول تحليل وتقرير'),
]


@dataclass
class ActivationProgress:
    group_id: str
    install_at: datetime | None
    stages: list[dict]            # [{stage, key, label, achieved_at, elapsed_hours}, ...]
    current_stage: int           # 1..4
    completed: bool
    elapsed_hours: float
    within_48h: bool
    shareable_banner_text: str

    def to_dict(self, lang: str = 'ar') -> dict:
        return {
            'group_id': self.group_id,
            'install_at': self.install_at.isoformat() if self.install_at else None,
            'stages': self.stages,
            'current_stage': self.current_stage,
            'completed': self.completed,
            'elapsed_hours': round(self.elapsed_hours, 2),
            'within_48h': self.within_48h,
            'shareable_banner_text': self.shareable_banner_text,
        }


async def compute_activation_progress(
    session: AsyncSession,
    company_group_id: str,
    lang: str = 'ar',
    now: datetime | None = None,
) -> ActivationProgress:
    """Read milestone rows and compute current progress.

    If no milestone rows exist yet, auto-derive them from observable data:
      - stage 1 = group.activation_started_at exists
      - stage 2 = any user exists in the group
      - stage 3 = any document exists in any company in the group
      - stage 4 = any AnalyticsOutput exists in any company in the group
    """
    group = (await session.execute(
        select(CompanyGroup).where(CompanyGroup.id == company_group_id)
    )).scalar_one_or_none()

    # Ensure milestone rows exist (idempotent)
    existing = (await session.execute(
        select(ActivationMilestone).where(ActivationMilestone.company_group_id == company_group_id)
    )).scalars().all()
    if not existing:
        # Auto-derive from observable data
        await _bootstrap_milestones(session, group)

    rows = (await session.execute(
        select(ActivationMilestone).where(ActivationMilestone.company_group_id == company_group_id).order_by(ActivationMilestone.stage)
    )).scalars().all()

    install_at = group.activation_started_at if group else None
    now = now or datetime.now(timezone.utc)
    stages = []
    current_stage = 1
    completed = False
    for stage, key, label in STAGES:
        row = next((r for r in rows if r.stage == stage), None)
        achieved = row.achieved_at if row else None
        elapsed = ((achieved - install_at).total_seconds() / 3600.0) if (achieved and install_at) else None
        stages.append({
            'stage': stage,
            'key': key,
            'label': label,
            'achieved_at': achieved.isoformat() if achieved else None,
            'elapsed_hours': round(elapsed, 2) if elapsed is not None else None,
        })
        if achieved is None and not completed:
            current_stage = stage
            break
        if achieved and stage == 4:
            completed = True
            current_stage = 4

    elapsed_hours = ((now - install_at).total_seconds() / 3600.0) if install_at else 0.0
    if completed:
        # Use time to stage 4 if available
        s4 = next((r for r in rows if r.stage == 4), None)
        if s4 and s4.achieved_at and install_at:
            elapsed_hours = (s4.achieved_at - install_at).total_seconds() / 3600.0
    within_48h = bool(completed and elapsed_hours <= 48)

    if lang == 'ar':
        banner = (
            f'تم تفعيل أول تقرير حقيقي خلال {elapsed_hours:.1f} ساعة'
            if completed else
            f'لم يكتمل التفعيل خلال 48 ساعة ({elapsed_hours:.1f} ساعة منقضية)'
        )
    else:  # ckb
        banner = (
            f'یەکەم ڕاپۆرتی ڕاستەقینە لە ماوەی {elapsed_hours:.1f} کاتژمێردا چالاک کرا'
            if completed else
            f'چالاککردن لە ماوەی ٤٨ کاتژمێردا تەواو نەبووە ({elapsed_hours:.1f} کاتژمێر تێپەڕیوە)'
        )

    return ActivationProgress(
        group_id=str(company_group_id),
        install_at=install_at,
        stages=stages,
        current_stage=current_stage,
        completed=completed,
        elapsed_hours=elapsed_hours,
        within_48h=within_48h,
        shareable_banner_text=banner,
    )


async def _bootstrap_milestones(session: AsyncSession, group: CompanyGroup | None) -> None:
    """Auto-derive stage achievements from observable data when no explicit
    milestone rows exist yet."""
    if group is None:
        return
    # Stage 1: activation_started_at set
    s1_at = group.activation_started_at if group.activation_started_at else None
    # Stage 2: any user in the group exists (created_at as proxy)
    from app.models.entities import User
    first_user = (await session.execute(
        select(User).where(User.company_group_id == group.id).order_by(User.created_at)
    )).scalars().first()
    s2_at = first_user.created_at if first_user else None
    # Stage 3: any document in any company in the group
    companies = (await session.execute(
        select(Company).where(Company.company_group_id == group.id)
    )).scalars().all()
    company_ids = [c.id for c in companies]
    first_doc = None
    if company_ids:
        first_doc = (await session.execute(
            select(Document).where(Document.company_id.in_(company_ids)).order_by(Document.created_at)
        )).scalars().first()
    s3_at = first_doc.created_at if first_doc else None
    # Stage 4: any AnalyticsOutput in the group
    first_analytics = None
    if company_ids:
        first_analytics = (await session.execute(
            select(AnalyticsOutput).where(AnalyticsOutput.company_id.in_(company_ids)).order_by(AnalyticsOutput.created_at)
        )).scalars().first()
    s4_at = first_analytics.created_at if first_analytics else None

    for stage, key, _label in STAGES:
        achieved_at = [s1_at, s2_at, s3_at, s4_at][stage - 1]
        session.add(ActivationMilestone(
            company_group_id=group.id,
            stage=stage,
            stage_key=key,
            achieved_at=achieved_at,
        ))
    await session.commit()


async def flag_overdue_installs(session: AsyncSession, sla_hours: int = 48) -> list[str]:
    """Return IDs of company_groups that have NOT completed activation within SLA."""
    flagged = []
    groups = (await session.execute(select(CompanyGroup))).scalars().all()
    now = datetime.now(timezone.utc)
    for g in groups:
        progress = await compute_activation_progress(session, str(g.id), now=now)
        if not progress.completed and progress.elapsed_hours > sla_hours:
            flagged.append(str(g.id))
    return flagged
