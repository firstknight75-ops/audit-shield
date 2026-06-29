"""Opportunity Map — untapped capability, IQD-priced upside.

Per AuditCore output #5: خريطة الفرص (Opportunity Map).
Distinct from Waste Map: waste = downside / leakage; opportunity = untapped upside.
IQD-priced per the platform convention.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Opportunity:
    kind: str          # vendor_underutilized | branch_underutilized | timing_mismatch
    description: str
    iqd_amount: int    # estimated upside in IQD
    confidence: str    # low | medium | high
    basis: dict        # raw numbers supporting the upside estimate


def build_opportunity_map(
    documents: list[dict],
    waste_items: list[dict],
    vendor_avg_iqd: dict[str, float] | None = None,
    branch_avg_iqd: dict[str, float] | None = None,
) -> list[Opportunity]:
    """Build opportunity items from raw certified documents + waste context.

    Heuristics (deterministic, explainable):
      - vendor_underutilized: a vendor with <30% of avg vendor volume, >0 spend → upside = avg - actual
      - branch_underutilized: a branch with <50% of avg branch spend → upside = avg - actual
      - timing_mismatch: if waste contains late-payment penalties, estimate refundable window
    """
    opps: list[Opportunity] = []

    if not documents:
        return opps

    # Vendor underutilization
    vendor_totals: dict[str, int] = defaultdict(int)
    for d in documents:
        v = d.get('vendor_name')
        a = d.get('amount') or 0
        if v and a:
            vendor_totals[v] += int(a)
    if vendor_totals and (vendor_avg_iqd is None or vendor_avg_iqd):
        avg = vendor_avg_iqd.get('__avg__') if vendor_avg_iqd else sum(vendor_totals.values()) / len(vendor_totals)
        for v, total in vendor_totals.items():
            if total < 0.30 * avg and total > 0:
                upside = int(avg - total)
                if upside > 0:
                    opps.append(Opportunity(
                        kind='vendor_underutilized',
                        description=f'مورّد بحجم منخفض: {v}',
                        iqd_amount=upside,
                        confidence='medium',
                        basis={'vendor': v, 'current_iqd': total, 'avg_iqd': int(avg), 'gap_iqd': upside},
                    ))

    # Branch underutilization
    branch_totals: dict[str, int] = defaultdict(int)
    for d in documents:
        b = d.get('branch_name') or d.get('branch_id')
        a = d.get('amount') or 0
        if b and a:
            branch_totals[str(b)] += int(a)
    if branch_totals:
        avg_branch = branch_avg_iqd.get('__avg__') if branch_avg_iqd else sum(branch_totals.values()) / len(branch_totals)
        for b, total in branch_totals.items():
            # A branch is "underutilized" if it's meaningfully below the avg.
            # We use a strict <50% threshold so quiet branches still surface
            # even when one branch dominates spend.
            if total < 0.50 * avg_branch and total > 0:
                upside = int(avg_branch - total)
                if upside > 0:
                    opps.append(Opportunity(
                        kind='branch_underutilized',
                        description=f'فرع بأداء منخفض: {b}',
                        iqd_amount=upside,
                        confidence='medium',
                        basis={'branch': b, 'current_iqd': total, 'avg_iqd': int(avg_branch), 'gap_iqd': upside},
                    ))

    # Timing mismatch — derive refundable window from any 'late_payment' waste items
    for w in waste_items:
        if (w.get('category') or '').lower() in ('late_payment', 'late_penalty'):
            amount = int(w.get('iqd_amount') or 0)
            if amount > 0:
                opps.append(Opportunity(
                    kind='timing_mismatch',
                    description='نافذة استرداد جزئية من غرامات التأخير',
                    iqd_amount=int(amount * 0.4),
                    confidence='low',
                    basis={'original_penalty_iqd': amount, 'recoverable_fraction': 0.4},
                ))

    # Cap at top 20 by IQD upside
    opps.sort(key=lambda o: o.iqd_amount, reverse=True)
    return opps[:20]


def opportunities_to_dict(opps: list[Opportunity]) -> list[dict]:
    return [
        {
            'kind': o.kind,
            'description': o.description,
            'iqd_amount': o.iqd_amount,
            'confidence': o.confidence,
            'basis': o.basis,
        }
        for o in opps
    ]


def total_upside_iqd(opps: list[Opportunity]) -> int:
    return sum(o.iqd_amount for o in opps)
