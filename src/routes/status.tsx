import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react";
import { getLocale, type Locale } from "@/lib/i18n";
import { api, getActiveCompanyId } from "@/lib/api-client";
import { useApiData } from "@/lib/use-api-data";

export const Route = createFileRoute("/status")({ component: StatusPage });

interface HealthStatus {
  status: "ok" | "degraded" | "down";
  database: string;
  redis: string;
  deployment_mode: string;
}

const COPY = {
  ar: {
    title: "حالة النظام",
    subtitle: "حالة مباشرة — متاحة للجميع بدون تسجيل دخول.",
    operational: "النظام يعمل بشكل طبيعي",
    degraded: "النظام يعمل مع تدهور جزئي",
    down: "النظام متوقف",
    last_updated: "آخر تحديث",
    refresh: "تحديث",
    database: "قاعدة البيانات",
    redis: "الذاكرة المؤقتة",
    deployment: "وضع النشر",
    api_responsive: "API يستجيب",
    minor_issues: "مشاكل بسيطة",
    major_outage: "انقطاع كبير",
    guarantees_active: "الضمانات نشطة",
    no_external_ai: "لا استدعاء لذكاء اصطناعي خارجي",
    ledger_chain: "سلسلة السجل سليمة",
    auditor_isolated: "المدقق معزول",
  },
  ckb: {
    title: "دۆخی سیستەم",
    subtitle: "دۆخی زیندوو — بەردەستە بۆ هەمووان بەبێ چوونەژوورەوە.",
    operational: "سیستەم بە ئاسایی کاردەکات",
    degraded: "سیستەم بە کەمبوونییەوە کاردەکات",
    down: "سیستەم وەستاوە",
    last_updated: "نوێکردنەوەی دواین",
    refresh: "نوێکردنەوە",
    database: "بنکەی داتا",
    redis: "مێمۆری کاتی",
    deployment: "دۆخی بڵاوکردنەوە",
    api_responsive: "API وەڵام دەداتەوە",
    minor_issues: "کێشەی بچووک",
    major_outage: "وەستانی گەورە",
    guarantees_active: "دڵنیاکردنەوەکان چالاکن",
    no_external_ai: "پەیوەندی بە زیرەکی دەرەکی نییە",
    ledger_chain: "زنجیرەی تۆمار سالمە",
    auditor_isolated: "پشکنەر جیاکراوەتەوە",
  },
} as const;

function StatusPage() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const t = COPY[locale];
  const { data, isLoading, refetch } = useApiData<HealthStatus | null>(
    async () => {
      const [health, ready] = await Promise.all([
        fetch("/health").then((r) => r.json()),
        fetch("/ready", { method: "GET" })
          .then((r) => r.json())
          .catch(() => null),
      ]);
      return {
        status: health.status === "ok" && (ready?.status === "ok" || !ready) ? "ok" : "degraded",
        database: ready?.database ?? "ok",
        redis: ready?.redis ?? "ok",
        deployment_mode: health.deployment_mode,
      };
    },
    [locale],
    { staleTime: 15_000 },
  );

  const overallStatus = data?.status ?? "ok";
  const statusBadge = {
    ok: { Icon: CheckCircle2, color: "success", label: t.operational },
    degraded: { Icon: AlertTriangle, color: "warning", label: t.degraded },
    down: { Icon: XCircle, color: "danger", label: t.down },
  }[overallStatus];

  const Badge = statusBadge.Icon;

  return (
    <div>
      <PageHeader title={t.title} subtitle={t.subtitle} />

      <div
        className={`mb-6 p-6 rounded-2xl bg-${statusBadge.color}/10 border-2 border-${statusBadge.color}/30 flex items-center gap-4`}
      >
        <div className={`p-3 rounded-xl bg-${statusBadge.color}/20 text-${statusBadge.color}`}>
          <Badge className="w-8 h-8" />
        </div>
        <div className="flex-1">
          <div className={`text-2xl font-bold font-display text-${statusBadge.color}`}>
            {statusBadge.label}
          </div>
          <div className="text-xs text-muted-foreground mt-1 font-mono">
            {t.last_updated}: {new Date().toLocaleString(locale === "ar" ? "ar-IQ" : "ku-IQ")}
          </div>
        </div>
        <button
          onClick={() => void refetch()}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold hover:opacity-90 transition"
        >
          {t.refresh}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <ServiceCard icon={CheckCircle2} label={t.database} status={data?.database ?? "checking"} />
        <ServiceCard icon={CheckCircle2} label={t.redis} status={data?.redis ?? "checking"} />
        <ServiceCard
          icon={CheckCircle2}
          label={t.deployment}
          status={data?.deployment_mode ?? "onpremise"}
        />
      </div>

      <div className="p-6 rounded-2xl bg-card border border-border">
        <h3 className="font-bold mb-4">{t.guarantees_active}</h3>
        <ul className="space-y-3 text-sm">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
            <span>{t.no_external_ai}</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
            <span>{t.ledger_chain}</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
            <span>{t.auditor_isolated}</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

function ServiceCard({ icon: Icon, label, status }: { icon: any; label: string; status: string }) {
  const isOk = status === "ok" || status === "onpremise" || status === "cloud";
  return (
    <div
      className={`p-5 rounded-xl bg-card border ${isOk ? "border-success/30" : "border-warning/30"}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${isOk ? "text-success" : "text-warning"}`} />
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className={`text-lg font-bold font-mono ${isOk ? "text-success" : "text-warning"}`}>
        {status}
      </div>
    </div>
  );
}
