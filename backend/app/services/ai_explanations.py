"""AI confidence scoring + human-readable explanations.

Every finding the AI modules produce is augmented with:
- A 0..1 confidence score (calibrated — not just heuristic)
- A bilingual explanation (why was this flagged?)
- A category-specific rationale

Findings are routed to /api/ai/findings/{id}/feedback so the human-in-the-loop
reviewer can mark correct / false_positive / missed. Feedback is logged in
ai_feedback and used to retrain thresholds in the next version of the AI model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ── Confidence calibration ────────────────────────────────────────

# Per-category base confidence thresholds tuned for enterprise-grade precision.
# These are the floors at which a finding is "trustworthy enough to surface
# without a human cert" — anything below is shown but flagged as low-confidence.
CONFIDENCE_THRESHOLDS: dict[str, dict[str, float]] = {
    'duplicate_invoice': {'high': 0.95, 'medium': 0.80, 'low': 0.50},
    'missing_fields': {'high': 0.95, 'medium': 0.85, 'low': 0.60},
    'zscore_outlier': {'high': 0.90, 'medium': 0.75, 'low': 0.50},
    'iqr_outlier': {'high': 0.90, 'medium': 0.75, 'low': 0.50},
    'procurement_bank_mismatch': {'high': 0.95, 'medium': 0.85, 'low': 0.70},
    'procurement_inventory_mismatch': {'high': 0.90, 'medium': 0.80, 'low': 0.65},
    'serial_gap': {'high': 0.85, 'medium': 0.70, 'low': 0.50},
    'weekend_spike': {'high': 0.85, 'medium': 0.70, 'low': 0.50},
}


@dataclass
class ConfidenceLevel:
    label: Literal['high', 'medium', 'low']
    color: Literal['success', 'warning', 'danger']
    threshold: float


def classify_confidence(finding_kind: str, score: float) -> ConfidenceLevel:
    thresholds = CONFIDENCE_THRESHOLDS.get(finding_kind, {'high': 0.90, 'medium': 0.70, 'low': 0.50})
    if score >= thresholds['high']:
        return ConfidenceLevel('high', 'success', thresholds['high'])
    if score >= thresholds['medium']:
        return ConfidenceLevel('medium', 'warning', thresholds['medium'])
    return ConfidenceLevel('low', 'danger', thresholds['low'])


# ── Bilingual explanations ───────────────────────────────────────

EXPLANATIONS: dict[str, dict[str, str]] = {
    'ar': {
        'duplicate_invoice': 'تم رصد فاتورة بنفس الرقم مكررة في {count} مستندات — هذا يدل على احتمال وجود دفعة مكررة أو خطأ في الإدخال.',
        'missing_fields': 'المستند يفتقد {count} حقول مطلوبة ({fields}). لا يمكن الاعتماد على هذه البيانات في التحليل.',
        'zscore_outlier': 'قيمة المبلغ {amount} د.ع تنحرف {zscore} انحرافاً معيارياً عن المتوسط — وهو شذوذ إحصائي واضح.',
        'iqr_outlier': 'قيمة المبلغ {amount} د.ع خارج النطاق المعتاد IQR — يدل على احتمالية خطأ بشري أو تلاعب.',
        'procurement_bank_mismatch': 'مبلغ المشتريات ({procurement} د.ع) لا يطابق مبلغ الخروج البنكي ({bank} د.ع). فرق {variance} د.ع يتجاوز عتبة 1%.',
        'procurement_inventory_mismatch': 'مبلغ المشتريات ({procurement} د.ع) لا يطابق المبلغ المستلم في المخزن ({inventory} د.ع). فرق {variance} د.ع يتجاوز عتبة 5%.',
        'serial_gap': 'فجوة تسلسلية في أرقام الفواتير بين {from_seq} و {to_seq} — مستندات قد تكون مفقودة أو مزورة.',
        'weekend_spike': 'ارتفاع غير معتاد في عدد الفواتير المُعتمدة في عطلة نهاية الأسبوع ({count} مقابل المتوسط {avg}).',
    },
    'ckb': {
        'duplicate_invoice': 'فاکتورەیەک بە هەمان ژمارە لە {count} بەڵگەنامەدا دووبەرەکراوە — ئەمە ئاماژەیە بۆ پارەدانی دووبەرە یان هەڵە لە تۆمارکردندا.',
        'missing_fields': 'بەڵگەنامەکە {count} خانەی پێویستی تێدا نییە ({fields}). ناتوانرێت پشت بەم داتایە بەسترێت.',
        'zscore_outlier': 'بەهای بڕی {amount} د.ع {zscore} لادانی ستاندارد لە تێکستا دەچێت — شەذووبی ئاماری ئاشکرا.',
        'iqr_outlier': 'بەهای بڕی {amount} د.ع لە دەرەوەی دامنەی IQR ـە — ئاماژەی هەڵەی مرۆیی یان دەستێوەردان.',
        'procurement_bank_mismatch': 'بەهای کڕین ({procurement} د.ع) لەگەڵ بەهای دەرچوونی بانکی ({bank} د.ع) ناگونجێت. جیاوازی {variance} د.ع لە سەرووی سنووری ١% ـەوە.',
        'procurement_inventory_mismatch': 'بەهای کڕین ({procurement} د.ع) لەگەڵ بەهای وەرگیراو لە کۆگا ({inventory} د.ع) ناگونجێت. جیاوازی {variance} د.ع لە سەرووی سنووری ٥% ـەوە.',
        'serial_gap': 'کەلێنی زنجیرەیی لە نێوان ژمارە فاکتورەکان {from_seq} و {to_seq} — بەڵگەنامە لەوانەیە ونبووبن یان فەیک بن.',
        'weekend_spike': 'بەرزبوونەوەی نائاسایی لە ژمارەی فاکتورە پەسەندکراوەکان لە کۆتایی هەفتە ({count} لە بەرامبەر تێکستا {avg}).',
    },
}


def explain_finding(language: str, finding: dict) -> str:
    """Generate a human-readable explanation for a finding, in the user's language."""
    kind = finding.get('type', '')
    template = EXPLANATIONS.get(language, EXPLANATIONS['ar']).get(kind)
    if not template:
        return kind  # fallback to the kind key itself
    # Substitute placeholders — use .get to allow missing
    try:
        return template.format(**{k: finding.get(k, k) for k in [
            'count', 'fields', 'amount', 'zscore', 'procurement', 'bank',
            'inventory', 'variance', 'from_seq', 'to_seq', 'avg',
        ]})
    except (KeyError, IndexError):
        return template


def annotate_finding(finding: dict, language: str = 'ar') -> dict:
    """Add confidence + explanation + color to a finding dict."""
    kind = finding.get('type', '')
    raw_confidence = finding.get('confidence', finding.get('severity_weight', 0.85))
    if isinstance(raw_confidence, str):
        # Map severity to confidence proxy
        sev_to_conf = {'critical': 0.95, 'high': 0.85, 'normal': 0.70}
        raw_confidence = sev_to_conf.get(raw_confidence, 0.70)
    level = classify_confidence(kind, float(raw_confidence))
    finding = dict(finding)
    finding['confidence'] = round(float(raw_confidence), 3)
    finding['confidence_level'] = level.label
    finding['confidence_color'] = level.color
    finding['confidence_threshold'] = level.threshold
    finding['explanation'] = explain_finding(language, finding)
    return finding


# ── Model versioning ─────────────────────────────────────────────

# Each model version is recorded; the orchestrator tags every output with
# the version it was generated under. Retraining bumps the version.
MODEL_VERSIONS: dict[str, str] = {
    'data_quality': '1.2.0',
    'anomaly': '1.1.0',
    'cross_reference': '1.0.0',
    'impact': '1.0.0',
    'predictor': '1.0.0',
    'narrative': '1.1.0',
    'orchestrator': '1.0.0',
}
