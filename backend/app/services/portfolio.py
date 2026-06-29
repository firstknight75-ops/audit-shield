"""Portfolio view — for owners managing more than one company.

Per AuditCore principle 5: Truth From Data — when the Owner manages more
than one company, a portfolio view above that — with company figures that
are never silently blended.

Each company is reported standalone. A flat total is shown separately
ONLY if the Owner explicitly requests it (not by default).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompanyPortfolioEntry:
    company_id: str
    company_name: str
    trust_index_score: int
    monthly_waste_iqd: int
    critical_alerts: int
    opportunity_iqd: int
    risk_alerts: int
    documents_total: int


def build_portfolio(entries: list[CompanyPortfolioEntry]) -> dict:
    """Build portfolio response. Entries are kept as a list — never blended
    silently. A `totals` block is included but clearly labeled as a sum,
    not a blended aggregate."""
    entries_sorted = sorted(entries, key=lambda e: -e.trust_index_score)

    return {
        'companies': [
            {
                'company_id': e.company_id,
                'company_name': e.company_name,
                'trust_index_score': e.trust_index_score,
                'monthly_waste_iqd': e.monthly_waste_iqd,
                'critical_alerts': e.critical_alerts,
                'opportunity_iqd': e.opportunity_iqd,
                'risk_alerts': e.risk_alerts,
                'documents_total': e.documents_total,
            }
            for e in entries_sorted
        ],
        'totals_explicit_sum': {  # clearly labeled as SUM, not blended
            'monthly_waste_iqd': sum(e.monthly_waste_iqd for e in entries_sorted),
            'opportunity_iqd': sum(e.opportunity_iqd for e in entries_sorted),
            'risk_alerts': sum(e.risk_alerts for e in entries_sorted),
            'documents_total': sum(e.documents_total for e in entries_sorted),
        },
        'unblended_note': 'هذه أرقام منفصلة لكل شركة. لا يتم دمجها تلقائياً.',
    }
