import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { auditorTasks } from "@/lib/mock-data";
import { getLocale, type Locale } from "@/lib/i18n";

export const Route = createFileRoute("/auditor/tasks")({ component: Tasks });

const TITLES: Record<Locale, { title: string; empty: string }> = {
  ar: { title: "مهامي اليومية", empty: "لا توجد مهام في نطاقك اليوم." },
  ckb: { title: "ئەرکە ڕۆژانەکانم", empty: "ئەمڕۆ هیچ ئەرکێک لە بواری تۆدا نییە." },
};

const STATUS: Record<
  Locale,
  { overdue: string; remaining: (m: number) => string; demerits: (p: number) => string }
> = {
  ar: {
    overdue: "متأخر",
    remaining: (m) => `متبقي ${m} د`,
    demerits: (p) => `+${p} نقاط سلبية`,
  },
  ckb: {
    overdue: "درەنگ",
    remaining: (m) => `${m} خولەک ماوە`,
    demerits: (p) => `+${p} خاڵی نەرێنی`,
  },
};

const SLA_TYPE: Record<Locale, string> = {
  ar: "موعد التسليم",
  ckb: "کۆتایی مۆڵەت",
};

function Tasks() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const done = auditorTasks.filter((t) => t.status === "done").length;
  const overdue = auditorTasks.filter((t) => t.status === "overdue").length;
  const demerits = auditorTasks.reduce((s, t) => s + t.demerits, 0);

  const summary =
    locale === "ar"
      ? `المنجزة: ${done} | المتأخرة: ${overdue} | النقاط السلبية: ${demerits}`
      : `تەواوبوو: ${done} | درەنگ: ${overdue} | خاڵی نەرێنی: ${demerits}`;

  if (auditorTasks.length === 0) {
    return (
      <div>
        <PageHeader title={TITLES[locale].title} />
        <div className="p-6 rounded-xl bg-card border border-border">{TITLES[locale].empty}</div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={TITLES[locale].title} subtitle={summary} />
      <div className="space-y-3">
        {auditorTasks.map((t) => {
          const overdueRow = t.status === "overdue";
          const t_status = STATUS[locale];
          return (
            <div
              key={t.id}
              className={`p-4 rounded-xl bg-card border ${overdueRow ? "border-danger/40" : "border-border"} flex items-center justify-between`}
            >
              <div className="flex items-center gap-4">
                <div
                  className={`w-2 h-12 rounded-full ${overdueRow ? "bg-danger" : t.remaining < 120 ? "bg-warning" : "bg-success"}`}
                />
                <div>
                  <div className="font-medium">{t.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {t.type} · {SLA_TYPE[locale]}: {t.sla}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div
                  className={`text-sm font-bold ${overdueRow ? "text-danger" : "text-foreground"}`}
                >
                  {overdueRow
                    ? `${t_status.overdue} ${Math.abs(t.remaining)} د`
                    : t_status.remaining(t.remaining)}
                </div>
                {t.demerits > 0 && (
                  <div className="text-xs text-danger mt-1">{t_status.demerits(t.demerits)}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
