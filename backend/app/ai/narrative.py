"""Narrative generation — bilingual (Arabic + Kurdish Sorani), audience-aware.

Per AuditCore Phase 3 spec:
- Arabic AND Sorani template-based narrative text
- Audience-aware: strategic phrasing for Owner, operational for Manager
- Pulled from Phase 1's translation tables (single source of truth)

The narrative is built deterministically from the AI findings — no
external LLM call, no chatbot — purely templated.
"""
from __future__ import annotations

import hashlib


# Deterministic locale-aware templates.
# Each language has its own strategic (owner) and operational (manager) phrasing.
# All amounts and counts are filled from the metrics + findings.
TEMPLATES = {
    'ar': {
        'owner': {
            'greeting': 'ملخص استراتيجي للمالك:',
            'waste_line': 'تم رصد هدر إجمالي قدره {waste:,.0f} د.ع خلال هذه الدورة.',
            'trust_high': 'مؤشر الثقة قوي عند {trust}/100 — الصورة الانعكاسية موثوقة.',
            'trust_mid': 'مؤشر الثقة متوسط عند {trust}/100 — يلزم تكيّف هيكلي لرفعه.',
            'trust_low': 'مؤشر الثقة منخفض عند {trust}/100 — البيانات لا تكفي لقرار تنفيذي بعد.',
            'critical_present': 'يوجد {n} تنبيهات حرجة تتطلب قراراً تنفيذياً سريعاً.',
            'critical_absent': 'لا توجد تنبيهات حرجة مفتوحة — العمل يسير ضمن نطاقه المتوقع.',
            'closing': 'هذه الصورة مبنية على {docs} مستند معتمد، ولا يمكن التلاعب بها بعد اعتمادها.',
        },
        'manager': {
            'greeting': 'ملخص تشغيلي للمدير:',
            'waste_line': 'الهدر التشغيلي في نطاقك يبلغ {waste:,.0f} د.ع.',
            'trust_high': 'مؤشر الثقة {trust}/100 — العمليات جارية ضمن المعايير.',
            'trust_mid': 'مؤشر الثقة {trust}/100 — راجع البنود الصفراء في قائمتك.',
            'trust_low': 'مؤشر الثقة {trust}/100 — يلزم تصحيح البنود الحمراء فوراً.',
            'critical_present': '{n} حالات حرجة تنتظر قرارك التشغيلي.',
            'critical_absent': 'لا حالات حرجة مفتوحة في نطاقك.',
            'closing': 'قائمتك تحتوي على {tasks} مهمة، منها {open} مفتوحة.',
        },
    },
    'ckb': {
        'owner': {
            'greeting': 'کورتی ستراتژی بۆ خاوەن:',
            'waste_line': 'کۆی بەفڕینی دۆزراوە {waste:,.0f} د.ع لەم خولەدا.',
            'trust_high': 'نیشاندەری متمانە بەرزە لە {trust}/100 — وێنەی ڕاستەقینە متمانەپێکراوە.',
            'trust_mid': 'نیشاندەری متمانە مامناوەندییە لە {trust}/100 — پێویستی بە گونجاندنی دەستەییە بۆ بەرزکردنەوەی.',
            'trust_low': 'نیشاندەری متمانە کەمە لە {trust}/100 — داتاکان بەس نین بۆ بڕیاری جێبەجێکار.',
            'critical_present': '{n} ئاگادارکردنەوەی ڕەخنەیی هەیە کە پێویستی بە بڕیاری خێرای جێبەجێکار هەیە.',
            'critical_absent': 'هیچ ئاگادارکردنەوەی ڕەخنەیی کراوە نییە — کار لە ناو چوارچێوەی چاوەڕوانکراوە.',
            'closing': 'ئەم وێنەیە لەسەر {docs} بەڵگەنامەی پەسندکراو دروستکراوە، و دوای پەسندکردن ناتوانرێت دەستکاری بکرێت.',
        },
        'manager': {
            'greeting': 'کورتی کارپێکردن بۆ بەڕێوەبەر:',
            'waste_line': 'بەفڕینی کارپێکردن لە بواری تۆدا {waste:,.0f} د.ع.',
            'trust_high': 'نیشاندەری متمانە {trust}/100 — کارەکان لە ناو پێوەرەکاندایە.',
            'trust_mid': 'نیشاندەری متمانە {trust}/100 — سەیری بڕگە زەردەکان لە لیستەکەت بکە.',
            'trust_low': 'نیشاندەری متمانە {trust}/100 — پێویستە بڕگە سوورەکان دەستبەجێ ڕاست بکرێنەوە.',
            'critical_present': '{n} حاڵەتی ڕەخنەیی چاوەڕێ بڕیاری کارپێکردنت دەکەن.',
            'critical_absent': 'هیچ حاڵەتی ڕەخنەیی کراوە لە بواری تۆدا نییە.',
            'closing': 'لیستەکەت {tasks} ئەرکی تێدایە، {open} دانەیان کراوە.',
        },
    },
}


def _lang() -> str:
    return 'ar'  # default; explicit per-call below


def _render(template: str, **kwargs) -> str:
    return template.format(**kwargs)


def generate_narrative(audience: str, metrics: dict, findings: list[dict], language: str = 'ar') -> str:
    """Generate the narrative for the given audience + language.

    Args:
        audience: 'owner' (strategic) or 'manager' (operational) or anything else (default operational).
        metrics: dict with 'monthly_waste', 'trust_index', 'total_documents' keys.
        findings: list of finding dicts from the AI modules.
        language: 'ar' (Arabic) or 'ckb' (Kurdish Sorani).
    """
    lang = language if language in TEMPLATES else 'ar'
    bucket = 'owner' if audience == 'owner' else 'manager'
    t = TEMPLATES[lang][bucket]

    waste = int(metrics.get('monthly_waste', 0) or 0)
    trust = int(metrics.get('trust_index', 0) or 0)
    critical_count = sum(1 for f in findings if f.get('severity') == 'critical')
    total_docs = int(metrics.get('total_documents', 0) or 0)
    open_tasks = int(metrics.get('open_tasks', 0) or 0)

    # Trust-level phrase
    if trust >= 80:
        trust_line = _render(t['trust_high'], trust=trust)
    elif trust >= 60:
        trust_line = _render(t['trust_mid'], trust=trust)
    else:
        trust_line = _render(t['trust_low'], trust=trust)

    # Critical alerts line
    if critical_count > 0:
        crit_line = _render(t['critical_present'], n=critical_count)
    else:
        crit_line = t['critical_absent']

    # Closing line is audience-specific
    if bucket == 'owner':
        closing = _render(t['closing'], docs=total_docs)
    else:
        closing = _render(t['closing'], tasks=open_tasks, open=open_tasks)

    return ' '.join([
        t['greeting'],
        _render(t['waste_line'], waste=waste),
        trust_line,
        crit_line,
        closing,
    ])


def narrative_hash(narrative: str) -> str:
    """Deterministic hash of the narrative — used for cache/dedupe checks."""
    return hashlib.sha256(narrative.encode('utf-8')).hexdigest()[:16]


# Backward-compat default: Arabic owner narrative
def generate_narrative_default(metrics: dict, findings: list[dict]) -> str:
    return generate_narrative('owner', metrics, findings, language='ar')
