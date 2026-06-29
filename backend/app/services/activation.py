"""48-Hour Activation Tracker.

Per AuditCore principle 7: first real report within 48 hours of installation,
tracked, not just promised.

Milestones:
  install          → CompanyGroup.created_at
  first_upload     → earliest Document.created_at for this tenant
  first_certified  → earliest OCRExtraction.certified_at for this tenant
  first_dashboard  → earliest AnalyticsOutput.created_at for this tenant
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ActivationMilestone:
    name: str
    achieved_at: datetime | None
    elapsed_hours_from_install: float | None


@dataclass
class ActivationStatus:
    install_at: datetime
    first_upload_at: datetime | None
    first_certified_at: datetime | None
    first_dashboard_at: datetime | None
    elapsed_hours: float
    within_48h: bool
    completed: bool  # dashboard generated = full activation

    def to_dict(self, lang: str = 'ar') -> dict:
        return {
            'install_at': self.install_at.isoformat() if self.install_at else None,
            'first_upload_at': self.first_upload_at.isoformat() if self.first_upload_at else None,
            'first_certified_at': self.first_certified_at.isoformat() if self.first_certified_at else None,
            'first_dashboard_at': self.first_dashboard_at.isoformat() if self.first_dashboard_at else None,
            'elapsed_hours': round(self.elapsed_hours, 2),
            'within_48h': self.within_48h,
            'completed': self.completed,
        }


def compute_activation_status(
    install_at: datetime,
    first_upload_at: datetime | None,
    first_certified_at: datetime | None,
    first_dashboard_at: datetime | None,
    now: datetime | None = None,
    sla_hours: int = 48,
) -> ActivationStatus:
    """Compute activation status vs SLA.

    `elapsed_hours` is measured from install to the LATEST achieved milestone
    if any milestone is achieved; otherwise to `now`.
    """
    now = now or datetime.now(timezone.utc)
    latest = first_dashboard_at or first_certified_at or first_upload_at
    if latest:
        elapsed = (latest - install_at).total_seconds() / 3600.0
    else:
        elapsed = (now - install_at).total_seconds() / 3600.0
    completed = first_dashboard_at is not None
    return ActivationStatus(
        install_at=install_at,
        first_upload_at=first_upload_at,
        first_certified_at=first_certified_at,
        first_dashboard_at=first_dashboard_at,
        elapsed_hours=elapsed,
        within_48h=completed and elapsed <= sla_hours,
        completed=completed,
    )
