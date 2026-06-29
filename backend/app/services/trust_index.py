"""Standalone Trust Index — first-class deliverable, not a dashboard card.

Per AuditCore principle 2 & output #2:
- مؤشر الموثوقية (Trust Index) is its own first-class deliverable.
- Calculated deterministically from data-quality findings.
- 0-100 score with explicit component breakdown.
- Every generation is recorded in the immutable ledger.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class TrustIndexComponents:
    coverage_pct: float          # % of documents with all 4 required fields
    duplicate_pct: float         # % of documents that are duplicates
    certified_pct: float         # % of documents certified by auditor
    missing_field_pct: float     # % of (document, field) pairs missing
    total_documents: int
    certified_documents: int
    duplicate_documents: int
    missing_fields_total: int

    @property
    def score(self) -> int:
        """Deterministic 0-100 score.

        Weighted components (sum = 100):
          coverage      : 35
          certified     : 30
          missing_field : 20  (higher is better)
          duplicate     : 15  (higher is better)

        When total_documents == 0, score is 0 (no data = no trust).
        """
        if self.total_documents <= 0:
            return 0
        cov = max(0.0, min(100.0, self.coverage_pct)) * 0.35
        cer = max(0.0, min(100.0, self.certified_pct)) * 0.30
        mis = max(0.0, min(100.0, 100.0 - self.missing_field_pct)) * 0.20
        dup = max(0.0, min(100.0, 100.0 - self.duplicate_pct)) * 0.15
        return int(round(cov + cer + mis + dup))

    @property
    def level(self) -> str:
        if self.score >= 80:
            return 'high'
        if self.score >= 60:
            return 'medium'
        return 'low'


def compute_trust_index(
    total_documents: int,
    certified_documents: int,
    duplicate_documents: int,
    missing_fields_total: int,
    required_field_slots: int = 4,
) -> TrustIndexComponents:
    """Compute Trust Index components from raw counts.

    `required_field_slots` defaults to 4: invoice_number, date, amount, vendor_name.
    """
    if total_documents <= 0:
        return TrustIndexComponents(
            coverage_pct=0.0,
            duplicate_pct=0.0,
            certified_pct=0.0,
            missing_field_pct=0.0,
            total_documents=0,
            certified_documents=0,
            duplicate_documents=0,
            missing_fields_total=missing_fields_total,
        )

    # coverage = % of docs that would have all required fields (100% - missing fraction)
    slots_total = total_documents * required_field_slots
    missing_pct = (missing_fields_total / slots_total * 100.0) if slots_total else 0.0
    coverage_pct = max(0.0, 100.0 - missing_pct)

    duplicate_pct = (duplicate_documents / total_documents) * 100.0
    certified_pct = (certified_documents / total_documents) * 100.0

    return TrustIndexComponents(
        coverage_pct=round(coverage_pct, 2),
        duplicate_pct=round(duplicate_pct, 2),
        certified_pct=round(certified_pct, 2),
        missing_field_pct=round(missing_pct, 2),
        total_documents=total_documents,
        certified_documents=certified_documents,
        duplicate_documents=duplicate_documents,
        missing_fields_total=missing_fields_total,
    )


def trust_index_to_dict(c: TrustIndexComponents) -> dict:
    return {
        'score': c.score,
        'level': c.level,
        'coverage_pct': c.coverage_pct,
        'certified_pct': c.certified_pct,
        'duplicate_pct': c.duplicate_pct,
        'missing_field_pct': c.missing_field_pct,
        'total_documents': c.total_documents,
        'certified_documents': c.certified_documents,
        'duplicate_documents': c.duplicate_documents,
        'missing_fields_total': c.missing_fields_total,
    }


def merge_findings_into_trust(
    findings: Iterable[dict],
    total_documents: int,
    certified_documents: int,
) -> TrustIndexComponents:
    """Derive Trust Index from raw AI findings (data-quality output).

    This is the production code path: feed in the output of
    `app.ai.data_quality.run_data_quality` plus counters from the
    certification flow.
    """
    findings = list(findings)
    duplicate_docs = len({f.get('document_id') for f in findings if f.get('type') == 'duplicate_invoice' and f.get('document_id')})
    missing_total = sum(len(f.get('missing_fields', []) or []) for f in findings if f.get('type') == 'missing_fields')
    return compute_trust_index(
        total_documents=total_documents,
        certified_documents=certified_documents,
        duplicate_documents=duplicate_docs,
        missing_fields_total=missing_total,
    )
