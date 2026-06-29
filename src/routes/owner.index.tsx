import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { TrendingDown, ShieldCheck, AlertTriangle, Wallet, Users, ArrowLeft, Briefcase } from "lucide-react";
import { getLocale, type Locale } from "@/lib/i18n";
import { ownerKpis, formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/")({ component: OwnerHome });

const COPY = {
  ar: {
    title: "الصورة الحقيقية",
    subtitle: "خمس حقائق فقط — كل حقيقة مرتبطة بمستند أصلي قابل للتتبع.",
    monthly_waste: "إجمالي الهدر الشهري",
    trust_index: "مؤشر الثقة",
    critical_alerts: "تنبيهات حرجة",
    predicted_cash: "الكاش المتوقع للشهر القادم",
    auditor_efficiency: "كفاءة فريق التدقيق",
    detail: "التفاصيل",
    multi_company_note: "لديك أكثر من شركة. اضغط على اسم الشركة في الأعلى للتنقل الجانبي.",
    single_company_note: "كل الأرقام التالية خاصة بهذه الشركة فقط.",
  },
  ckb: {
    title: "وێنەی ڕاستەقینە",
    subtitle: "تەنها پێنج ڕاستی — هەر ڕاستییەک بە بەڵگەنامەی ئەسڵی دەتوانرێت بەدواداچوونی بۆ بکرێت.",
    monthly_waste: "کۆی بەفڕینی مانگانە",
    trust_index: "نیشاندەری متمانە",
    critical_alerts: "ئاگادارکردنەوەی ڕەخنەیی",
    predicted_cash: "پارەی چاوەڕوانکراو بۆ مانگی داهاتوو",
    auditor_efficiency: "کارایی تیمی پشکنین",
    detail: "وردەکاری",
    multi_company_note: "زیاتر لە یەک کۆمپانیات هەیە. پەنجە لە ناوی کۆمپانیاکە لە سەرەوە بکە بۆ گەشتکردنی لاتەنیشت.",
    single_company_note: "هەموو ژمارەکانی خوارەوە تایبەتن بەم کۆمپانیایە تەنها.",
  },
} as const;

const toneClass: Record<string, string> = {
  danger: "text-danger border-danger/30 bg-danger/5",
  warning: "text-warning border-warning/30 bg-warning/5",
  success: "text-success border-success/30 bg-success/5",
  primary: "text-primary border-primary/30 bg-primary/5",
};

function OwnerHome() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const t = COPY[locale];

  // Executive layer — exactly 5 cards per Phase 3 spec
  const cards = [
    { key: "waste", label: t.monthly_waste, value: formatIQD(ownerKpis.monthlyWaste), icon: TrendingDown, tone: "danger", to: "/owner/waste-map" },
    { key: "trust", label: t.trust_index, value: `${ownerKpis.trustIndex} / 100`, icon: ShieldCheck, tone: "success", to: "/owner/trust-index" },
    { key: "alerts", label: t.critical_alerts, value: String(ownerKpis.criticalAlerts), icon: AlertTriangle, tone: "warning", to: "/owner/risk-map" },
    { key: "cash", label: t.predicted_cash, value: formatIQD(ownerKpis.predictedCash), icon: Wallet, tone: "primary", to: "/owner/what-if" },
    { key: "eff", label: t.auditor_efficiency, value: `${ownerKpis.auditorEfficiency}%`, icon: Users, tone: "primary", to: "/owner/ledger" },
  ];

  return (
    <div>
      <PageHeader title={t.title} subtitle={t.subtitle} />

      {/* Note for multi-company owners */}
      <div className="mb-6 p-4 rounded-xl bg-primary/5 border border-primary/30 flex items-center gap-3 text-sm">
        <Briefcase className="w-4 h-4 text-primary shrink-0" />
        <span>{t.multi_company_note}</span>
      </div>

      {/* EXACTLY 5 CARDS — Phase 3 Executive layer */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <Link
              key={c.key}
              to={c.to}
              className={`group p-5 rounded-2xl bg-card border border-border hover:border-primary transition relative overflow-hidden`}
            >
              <div className={`inline-flex p-2 rounded-lg border ${toneClass[c.tone]}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="text-sm text-muted-foreground mt-4">{c.label}</div>
              <div className="text-2xl font-bold font-display mt-2">{c.value}</div>
              <div className="flex items-center gap-1 text-xs text-primary mt-4 opacity-0 group-hover:opacity-100 transition">
                {t.detail} <ArrowLeft className="w-3 h-3" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Reuse the existing chart/recommendations structure */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl bg-card border border-border">
          <h3 className="font-bold mb-4">
            {locale === "ar" ? "التدفق النقدي — آخر 6 أشهر (مليون د.ع)" : "ڕەوتی نەقدی — ٦ مانگی دواین (ملیۆن د.ع)"}
          </h3>
          <div className="text-sm text-muted-foreground">{t.single_company_note}</div>
        </div>
        <div className="p-6 rounded-xl bg-card border border-border">
          <h3 className="font-bold mb-4">
            {locale === "ar" ? "المسار الموصى به" : "ڕێڕەوی پێشنیارکراو"}
          </h3>
          <ol className="space-y-4 text-sm">
            {[
              locale === "ar" ? "مراجعة 7 تنبيهات حرجة في خريطة المخاطر" : "پێداچوونەوەی ٧ ئاگادارکردنەوەی ڕەخنەیی لە نەخشەی مەترسییەکان",
              locale === "ar" ? "تأكيد توصية استرداد 12.4 مليون د.ع" : "دووبەرەکرنی ڕاسپاردەی گەڕاندنەوەی ١٢٫٤ ملیۆن د.ع",
              locale === "ar" ? "اطّلاع على تقرير الأداء الأسبوعي للمدققين" : "سەیری ڕاپۆرتی کارایی هەفتانەی پشکنەران",
              locale === "ar" ? "تشغيل محاكي القرار للقرار الشهري الكبير" : "کارپێکردنی هاوشێوەکاری بڕیار بۆ بڕیاری گەورەی مانگانە",
            ].map((s, i) => (
              <li key={i} className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-primary/15 text-primary text-xs flex items-center justify-center font-bold shrink-0">{i + 1}</span>
                <span className="leading-relaxed">{s}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
