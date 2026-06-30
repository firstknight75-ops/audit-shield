import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { getLocale, type Locale } from "@/lib/i18n";
import { api, getActiveCompanyId } from "@/lib/api-client";
import { useApiData } from "@/lib/use-api-data";

export const Route = createFileRoute("/owner/trust-index")({ component: TrustIndexPage });

interface TrendPoint { cycle: string; score: number }
interface TrustIndexData {
  score: number;
  coverage_pct: number;
  certified_pct: number;
  certified_documents: number;
  total_documents: number;
  missing_field_pct: number;
  missing_fields_total: number;
  duplicate_pct: number;
  duplicate_documents: number;
  trend?: TrendPoint[];
  generatedAt?: string;
}

const COPY = {
  ar: {
    title: "مؤشر الثقة",
    subtitle: "صحة بيانات شركتك في رقم واحد.",
    score_label: "النقاط",
    coverage_label: "التغطية",
    certified_label: "المعتمد",
    missing_label: "حقول ناقصة",
    duplicate_label: "مكررات",
    trend_6: "آخر 6 دورات",
    last_run: "آخر تحديث",
  },
  ckb: {
    title: "نیشاندەری متمانە",
    subtitle: "تەندروستی داتای کۆمپانیاکەت لە یەک ژمارەدا.",
    score_label: "خاڵ",
    coverage_label: "گشتگیری",
    certified_label: "ڕەسمی",
    missing_label: "خانە کەمکراوەکان",
    duplicate_label: "دووبارە",
    trend_6: "٦ دەوری کۆتایی",
    last_run: "نوێکردنەوەی دواین",
  },
} as const;

function Tile({ label, value, sub, tone }: { label: string; value: string; sub: string; tone: string }) {
  const toneText: Record<string, string> = {
    primary: "text-primary", success: "text-success", warning: "text-warning", danger: "text-danger",
  };
  return (
    <div className="p-5 rounded-2xl bg-card border border-border">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`text-3xl font-bold font-display mt-2 ${toneText[tone]}`}>{value}</div>
      <div className="text-xs text-muted-foreground mt-1">{sub}</div>
    </div>
  );
}

function TrustIndexPage() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  const [companyId, setCompanyId] = useState<string | null>(null);
  
  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    const onCompanyChanged = () => {
      setCompanyId(getActiveCompanyId());
    };
    window.addEventListener("storage", onStorage);
    window.addEventListener("auditcore.active_company_changed", onCompanyChanged);
    onCompanyChanged();
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("auditcore.active_company_changed", onCompanyChanged);
    };
  }, []);

  const t = COPY[locale];
  void setLocale;

  const { data } = useApiData<TrustIndexData | null>(
    async () => {
      if (!companyId) return null;
      const res = await api.owner.trustIndex(companyId) as Record<string, unknown>;
      return {
        score: Number(res.score ?? 0),
        coverage_pct: Number(res.coverage_pct ?? 0),
        certified_pct: Number(res.certified_pct ?? 0),
        certified_documents: Number(res.certified_documents ?? 0),
        total_documents: Number(res.total_documents ?? 0),
        missing_field_pct: Number(res.missing_field_pct ?? 0),
        missing_fields_total: Number(res.missing_fields_total ?? 0),
        duplicate_pct: Number(res.duplicate_pct ?? 0),
        duplicate_documents: Number(res.duplicate_documents ?? 0),
        trend: (res.trend as TrendPoint[] | undefined) ?? [],
        generatedAt: res.generated_at as string | undefined,
      };
    },
    [companyId],
    { enabled: !!companyId, staleTime: 60_000 },
  );

  if (!data) {
    return (
      <div>
        <PageHeader title={t.title} subtitle={t.subtitle} />
        <div className="p-8 rounded-2xl bg-card border border-border text-muted-foreground text-sm">…</div>
      </div>
    );
  }

  const meta = data.score >= 80
    ? { color: "success", label: locale === "ar" ? "ممتاز" : "نایاب", ring: "border-success/30" }
    : data.score >= 60
    ? { color: "warning", label: locale === "ar" ? "جيد" : "باش", ring: "border-warning/30" }
    : { color: "danger", label: locale === "ar" ? "يحتاج تحسين" : "پێویستی بە باشترکردن هەیە", ring: "border-danger/30" };

  const ringStroke = meta.color === "success" ? "var(--success)" : meta.color === "warning" ? "var(--warning)" : "var(--danger)";

  return (
    <div>
      <PageHeader title={t.title} subtitle={t.subtitle} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1 p-8 rounded-2xl bg-card border border-border flex flex-col items-center justify-center">
          <div className="relative w-44 h-44">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              <circle cx="50" cy="50" r="42" fill="none" stroke="oklch(0.32 0.03 250)" strokeWidth="10" />
              <circle cx="50" cy="50" r="42" fill="none" stroke={ringStroke} strokeWidth="10"
                strokeDasharray={`${(data.score / 100) * 264} 264`} strokeLinecap="round" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-4xl font-bold font-display">{data.score}</div>
              <div className="text-xs text-muted-foreground">{t.score_label}</div>
            </div>
          </div>
          <div className={`inline-flex items-center gap-1 mt-3 px-3 py-1 rounded-full bg-${meta.color}/15 text-${meta.color} border ${meta.ring} text-sm font-bold`}>
            <ShieldCheck className="w-3 h-3" /> {meta.label}
          </div>
          {data.generatedAt && (
            <div className="text-xs text-muted-foreground mt-3 font-mono">{t.last_run}: {data.generatedAt}</div>
          )}
        </div>
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <Tile label={t.coverage_label} value={`${data.coverage_pct}%`} sub={`${data.total_documents} ${locale === "ar" ? "مستند" : "بەڵگەنامە"}`} tone="primary" />
          <Tile label={t.certified_label} value={`${data.certified_pct}%`} sub={`${data.certified_documents} / ${data.total_documents}`} tone="success" />
          <Tile label={t.missing_label} value={`${data.missing_field_pct}%`} sub={`${data.missing_fields_total} ${locale === "ar" ? "حقل" : "خانە"}`} tone="warning" />
          <Tile label={t.duplicate_label} value={`${data.duplicate_pct}%`} sub={`${data.duplicate_documents} ${locale === "ar" ? "مستند" : "بەڵگەنامە"}`} tone="danger" />
        </div>
      </div>
      <div className="p-6 rounded-2xl bg-card border border-border">
        <h3 className="font-bold mb-4">{t.trend_6}</h3>
        <div className="grid grid-cols-6 gap-3">
          {(data.trend ?? []).map((point, i) => (
            <div key={i} className="text-center">
              <div className="text-xs text-muted-foreground mb-1">{point.cycle}</div>
              <div className={`text-2xl font-bold font-display ${point.score >= 80 ? "text-success" : point.score >= 60 ? "text-warning" : "text-danger"}`}>
                {point.score}
              </div>
              <div className="h-2 rounded-full bg-secondary overflow-hidden mt-2">
                <div className={`h-full bg-${point.score >= 80 ? "success" : point.score >= 60 ? "warning" : "danger"}`} style={{ width: `${point.score}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
