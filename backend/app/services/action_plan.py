"""Action Plan — Change path + Adaptation path.

Per AuditCore output #6: خطة العمل (Action Plan).
- Change path: prioritized items to fix NOW (from waste map, by IQD impact).
- Adaptation path: structural recommendations based on actual data patterns.
Both are deterministic, explainable, and priced in IQD.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ActionItem:
    path: str         # 'change' | 'adaptation'
    title: str
    rationale: str
    priority: int     # 1 (highest) .. 5 (lowest)
    deadline_days: int
    estimated_iqd: int  # positive = recovered upside
    source_finding: dict | None = None
    owner_role: str = 'manager'


def build_change_path(waste_items: list[dict], top_n: int = 5) -> list[ActionItem]:
    """Top-N waste items, prioritized by IQD amount, with sensible deadlines."""
    sorted_waste = sorted(
        [w for w in waste_items if int(w.get('iqd_amount') or 0) > 0],
        key=lambda w: int(w.get('iqd_amount') or 0),
        reverse=True,
    )[:top_n]
    actions: list[ActionItem] = []
    for i, w in enumerate(sorted_waste, start=1):
        iqd = int(w.get('iqd_amount') or 0)
        actions.append(ActionItem(
            path='change',
            title=f'معالجة: {w.get("category", "غير مصنف")} — {w.get("description", "")[:80]}',
            rationale=f'تم اكتشاف هذا البند بقيمة {iqd:,} د.ع في خريطة الهدر.',
            priority=min(i, 5),
            deadline_days=14 if i == 1 else (21 if i == 2 else 30),
            estimated_iqd=iqd,
            source_finding=w,
            owner_role='manager',
        ))
    return actions


def build_adaptation_path(
    waste_items: list[dict],
    trust_level: str,
    coverage_pct: float,
) -> list[ActionItem]:
    """Structural recommendations derived from waste pattern + trust level."""
    adaptations: list[ActionItem] = []

    # 1. Coverage-driven recommendation
    if coverage_pct < 70:
        adaptations.append(ActionItem(
            path='adaptation',
            title='تحسين تغطية رفع المستندات في الفروع منخفضة التغطية',
            rationale=f'التغطية الحالية {coverage_pct:.1f}% — رفعها يحسن مؤشر الموثوقية.',
            priority=2,
            deadline_days=45,
            estimated_iqd=0,
            owner_role='gm',
        ))

    # 2. Trust-level-driven recommendation
    if trust_level == 'low':
        adaptations.append(ActionItem(
            path='adaptation',
            title='إعادة جدولة عملية الاعتماد اليومية',
            rationale='مؤشر الموثوقية منخفض — يستلزم تكيّف هيكلي في دورة الاعتماد.',
            priority=1,
            deadline_days=21,
            estimated_iqd=0,
            owner_role='gm',
        ))

    # 3. Duplicate-heavy waste
    dup_count = sum(1 for w in waste_items if (w.get('category') or '').lower() in ('duplicate', 'duplicate_invoice'))
    if dup_count >= 2:
        adaptations.append(ActionItem(
            path='adaptation',
            title='تطبيق قاعدة منع تكرار رقم الفاتورة على مستوى النظام',
            rationale=f'تم رصد {dup_count} حالات تكرار — يستلزم ضبط هيكلي.',
            priority=2,
            deadline_days=30,
            estimated_iqd=0,
            owner_role='admin',
        ))

    # 4. Timing-mismatch heavy
    timing_count = sum(1 for w in waste_items if (w.get('category') or '').lower() in ('late_payment', 'late_penalty'))
    if timing_count >= 2:
        adaptations.append(ActionItem(
            path='adaptation',
            title='إعادة هيكلة جدول الدفعات الأسبوعية',
            rationale=f'{timing_count} حالات تأخير — يستلزم تكيّف هيكلي في التدفق النقدي.',
            priority=3,
            deadline_days=45,
            estimated_iqd=0,
            owner_role='gm',
        ))

    return adaptations


def action_items_to_dict(items: list[ActionItem]) -> list[dict]:
    return [
        {
            'path': a.path,
            'title': a.title,
            'rationale': a.rationale,
            'priority': a.priority,
            'deadline_days': a.deadline_days,
            'estimated_iqd': a.estimated_iqd,
            'owner_role': a.owner_role,
            'source_finding': a.source_finding,
        }
        for a in items
    ]
