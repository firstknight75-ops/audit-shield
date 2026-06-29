import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { ErrorBoundary } from "@/components/error-boundary";
import { ExecutiveSkeleton, AnalyzingMessage } from "@/components/loading-skeleton";
import { TrendingDown, ShieldCheck, AlertTriangle, Wallet, Users, ArrowLeft, Briefcase, RefreshCw, Sparkles } from "lucide-react";
import { getLocale, type Locale } from "@/lib/i18n";
import { api, getActiveCompanyId } from "@/lib/api-client";
import { useApiData } from "@/lib/use-api-data";

export const Route = createFileRoute("/owner/")({ component: OwnerHome });

interface ExecutiveKpis {
  monthlyWaste: number;
  trustIndex: number;
  criticalAlerts: number;
  predictedCash: number;
  auditorEfficiency: number;
  narrative?: string;
  generatedAt?: string;
}

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
    retraining: "إعادة التحليل",
    analyzing: "جاري تحليل البيانات...",
    error: "تعذّر تحميل البيانات. تحقق من اتصال الشبكة.",
    retry: "إعادة المحاولة",
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
    retraining: "دووبەرەکرنەوەی شیکاری",
    analyzing: "لە شیکردنەوەی داتاکاندا...",
    error: "بارکردنی داتاکان سەرکەوتوو نەبوو. پەیوەندی خۆت بپشکنە.",
    retry: "هەوڵکردنەوە",
  },
} as const;

// tone → icon chip styling + soft glow color used for the card hover aura
const toneClass: Record<string, string> = {
  danger: "text-danger border-danger/30 bg-danger/5",
  warning: "text-warning border-warning/30 bg-warning/5",
  success: "text-success border-success/30 bg-success/5",
  primary: "text-primary border-primary/30 bg-primary/5",
};
const toneGlow: Record<string, string> = {
  danger: "group-hover:shadow-[0_12px_40px_-16px_var(--danger)]",
  warning: "group-hover:shadow-[0_12px_40px_-16px_var(--warning)]",
  success: "group-hover:shadow-[0_12px_40px_-16px_var(--success)]",
  primary: "group-hover:shadow-[0_12px_40px_-16px_var(--primary)]",
};
const toneBar: Record<string, string> = {
  danger: "bg-danger",
  warning: "bg-warning",
  success: "bg-success",
  primary: "bg-primary",
};

function formatIQD(n: number, locale: Locale): string {
  return new Intl.NumberFormat(locale === "ar" ? "ar-IQ" : "ku-IQ", {
    style: "decimal",
    maximumFractionDigits: 0,
  }).format(n) + " د.ع";
}

function OwnerHome() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  const [companyId, setCompanyId] = useState<string | null>(null);

  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    window.addEventListener("storage", onStorage);
    setCompanyId(getActiveCompanyId());
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const t = COPY[locale];

  // ── Real API integration (UNCHANGED) ─────────────────────────────
  const { data, error, isLoading, refetch, isStale } = useApiData<ExecutiveKpis | null>(
    async () => {
      if (!companyId) return null;
      const me = await api.auth.me();
      if (me.accessible_companies.length === 0) return null;
      const cid = companyId || me.accessible_companies[0].company_id;
      const picture = await api.owner.picture(cid) as Record<string, unknown>;
      return {
        monthlyWaste: Number(picture.monthly_waste_iqd ?? 0),
        trustIndex: Number(picture.trust_index_score ?? 0),
        criticalAlerts: Number(picture.critical_alerts ?? 0),
        predictedCash: Number(picture.predicted_cash_outflow_iqd ?? 0),
        auditorEfficiency: Number(picture.auditor_efficiency ?? 0),
        narrative: picture.narrative as string | undefined,
        generatedAt: picture.generated_at as string | undefined,
      };
    },
    [companyId, locale],
    { enabled: !!companyId, staleTime: 60_000 },
  );

  // Executive layer — exactly 5 cards per Phase 3 spec (UNCHANGED logic)
  const cards = data
    ? [
        { key: "waste", label: t.monthly_waste, value: formatIQD(data.monthlyWaste, locale), icon: TrendingDown, tone: "danger", to: "/owner/waste-map" },
        { key: "trust", label: t.trust_index, value: `${data.trustIndex} / 100`, icon: ShieldCheck, tone: data.trustIndex >= 80 ? "success" : data.trustIndex >= 60 ? "warning" : "danger", to: "/owner/trust-index" },
        { key: "alerts", label: t.critical_alerts, value: String(data.criticalAlerts), icon: AlertTriangle, tone: "warning", to: "/owner/risk-map" },
        { key: "cash", label: t.predicted_cash, value: formatIQD(data.predictedCash, locale), icon: Wallet, tone: "primary", to: "/owner/what-if" },
        { key: "eff", label: t.auditor_efficiency, value: `${data.auditorEfficiency}%`, icon: Users, tone: "primary", to: "/owner/ledger" },
      ]
    : [];

  if (error) {
    return (
      <div>
        <PageHeader title={t.title} subtitle={t.subtitle} />
        <div className="p-6 rounded-2xl bg-danger/5 border border-danger/30">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-danger shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-bold text-danger">{t.error}</div>
              {error instanceof Error && "request_id" in error && (error as { request_id: string | null }).request_id && (
                <div className="text-xs text-muted-foreground mt-1 font-mono">
                  request_id: {(error as { request_id: string | null }).request_id}
                </div>
              )}
              <button onClick={() => void refetch()} className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-bold transition-all hover:bg-primary/90 hover:shadow-[0_4px_20px_-4px_var(--primary)] active:scale-[0.98]">
                <RefreshCw className="w-4 h-4" /> {t.retry}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={t.title} subtitle={t.subtitle} />

      <div className="mb-6 p-4 rounded-2xl bg-gradient-to-l from-primary/10 to-primary/0 border border-primary/25 flex items-center gap-3 text-sm">
        <Briefcase className="w-4 h-4 text-primary shrink-0" />
        <span>{t.multi_company_note}</span>
      </div>

      {isLoading || isStale ? <ExecutiveSkeleton /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
          {cards.map((c) => {
            const Icon = c.icon;
            return (
              <Link
                key={c.key}
                to={c.to}
                className={`group relative overflow-hidden p-5 rounded-2xl border border-border bg-gradient-to-b from-card to-card/60 transition-all duration-300 hover:-translate-y-1 hover:border-primary/60 ${toneGlow[c.tone]}`}
              >
                {/* accent top bar */}
                <span className={`absolute inset-x-0 top-0 h-1 ${toneBar[c.tone]} opacity-60 group-hover:opacity-100 transition`} />
                <div className={`inline-flex p-2.5 rounded-xl border ${toneClass[c.tone]}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="text-sm text-muted-foreground mt-4">{c.label}</div>
                <div className="text-2xl font-bold font-display mt-2 tracking-tight">{c.value}</div>
                <div className="flex items-center gap-1 text-xs text-primary mt-4 translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all">
                  {t.detail} <ArrowLeft className="w-3 h-3" />
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* AI narrative — strategic for Owner */}
      {data?.narrative && (
        <div className="trust-card p-6 rounded-2xl bg-gradient-to-bl from-primary/8 to-card border border-primary/25 mb-6">
          <div className="flex items-start gap-3">
            <div className="inline-flex p-2 rounded-xl border border-primary/30 bg-primary/10 text-primary shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <div className="text-xs uppercase tracking-wide text-primary/80 mb-2 font-bold">
                {locale === "ar" ? "ملخص استراتيجي للمالك" : "کورتی ستراتژی بۆ خاوەن"}
              </div>
              <p className="text-base leading-relaxed">{data.narrative}</p>
              {data.generatedAt && (
                <div className="text-xs text-muted-foreground mt-3 font-mono">
                  {locale === "ar" ? "آخر تحديث:" : "نوێکردنەوەی دواین:"} {data.generatedAt}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!isLoading && (
        <div className="p-6 rounded-2xl bg-card border border-border">
          <h3 className="font-bold font-display mb-5 flex items-center gap-2">
            <span className="w-1 h-5 rounded-full bg-primary" />
            {locale === "ar" ? "الإجراءات التالية الموصى بها" : "کارەکانی دواتر پێشنیارکراو"}
          </h3>
          <ol className="space-y-4 text-sm">
            {[
              locale === "ar" ? "مراجعة 7 تنبيهات حرجة في خريطة المخاطر" : "پێداچوونەوەی ٧ ئاگادارکردنەوەی ڕەخنەیی لە نەخشەی مەترسییەکان",
              locale === "ar" ? "تأكيد توصية استرداد 12.4 مليون د.ع" : "دووبەرەکرنی ڕاسپاردەی گەڕاندنەوەی ١٢٫٤ ملیۆن د.ع",
              locale === "ar" ? "اطّلاع على تقرير الأداء الأسبوعي للمدققين" : "سەیری ڕاپۆرتی کارایی هەفتانەی پشکنەران",
              locale === "ar" ? "تشغيل محاكي القرار للقرار الشهري الكبير" : "کارپێکردنی هاوشێوەکاری بڕیار بۆ بڕیاری گەورەی مانگانە",
            ].map((s, i) => (
              <li key={i} className="flex gap-3 items-start group">
                <span className="w-7 h-7 rounded-full bg-primary/15 text-primary text-xs flex items-center justify-center font-bold shrink-0 border border-primary/20 group-hover:bg-primary group-hover:text-primary-foreground transition">{i + 1}</span>
                <span className="leading-relaxed pt-0.5">{s}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
