from __future__ import annotations


def generate_narrative(audience: str, metrics: dict, findings: list[dict]) -> str:
    waste = int(metrics.get('monthly_waste', 0))
    trust = int(metrics.get('trust_index', 0))
    critical = len([f for f in findings if f.get('severity') == 'critical'])
    if audience == 'owner':
        return f'ملخص استراتيجي: تم رصد هدر مقداره {waste} دينار عراقي، ومؤشر الثقة الحالي هو {trust} من 100، مع {critical} تنبيهات حرجة تتطلب قراراً تنفيذياً سريعاً.'
    return f'ملخص تشغيلي: يوجد هدر تشغيلي بقيمة {waste} دينار، ومؤشر الثقة {trust}/100. الأولوية الآن لمعالجة {critical} حالات حرجة داخل نطاق التشغيل.'
