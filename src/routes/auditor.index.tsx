import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { AuditorOnboarding } from "@/components/auditor-onboarding";
import { sampleInvoice } from "@/lib/mock-data";
import { getLocale, type Locale } from "@/lib/i18n";
import { CheckCircle2, AlertCircle, XCircle, FileText } from "lucide-react";

export const Route = createFileRoute("/auditor/")({ component: AuditorCert });

const COLOR_COPY: Record<Locale, { green: string; yellow: string; red: string }> = {
  ar: { green: "أخضر", yellow: "أصفر", red: "أحمر" },
  ckb: { green: "سەوز", yellow: "زەرد", red: "سوور" },
};

const CERTIFY_BUTTON: Record<Locale, string> = {
  ar: "تأكيد واعتماد المستند",
  ckb: "دووبەرەکرن و پەسندکردنی بەڵگەنامە",
};

const CERTIFIED_AND_NEXT: Record<Locale, string> = {
  ar: "تم اعتماد المستند وتحميل التالي تلقائياً.",
  ckb: "بەڵگەنامە پەسند کرا و دواترین بە خۆکار بارکرا.",
};

const NO_PENDING: Record<Locale, string> = {
  ar: "لا توجد مستندات في نطاقك.",
  ckb: "هیچ بەڵگەنامەیەک لە بواری تۆدا نییە.",
};

function flagFor(conf: number, locale: Locale) {
  if (conf >= 85) return { tone: "success", Icon: CheckCircle2, label: COLOR_COPY[locale].green };
  if (conf >= 60) return { tone: "warning", Icon: AlertCircle, label: COLOR_COPY[locale].yellow };
  return { tone: "danger", Icon: XCircle, label: COLOR_COPY[locale].red };
}

function AuditorCert() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const [queue, setQueue] = useState([sampleInvoice, { ...sampleInvoice, id: "d2", filename: "INV-2026-0482.pdf" }]);
  const current = queue[0];
  const [fields, setFields] = useState(current.fields);
  const [done, setDone] = useState(false);
  const unresolved = fields.some((f) => f.confidence < 85 && String(f.value).trim() === "");

  const certify = () => {
    setDone(true);
    const nextQueue = queue.slice(1);
    setQueue(nextQueue);
    if (nextQueue[0]) setFields(nextQueue[0].fields);
    setTimeout(() => setDone(false), 1800);
  };

  return (
    <div>
      <PageHeader
        title={locale === "ar" ? "منصة اعتماد المستندات" : "پلاتفۆڕمی پەسندکردنی بەڵگەنامە"}
        subtitle={
          locale === "ar"
            ? "لا يتم اعتماد أي نتيجة OCR تلقائياً. يجب على المدقق مراجعة وتصحيح الحقول الصفراء والحمراء أولاً."
            : "هیچ ئەنجامی OCR بە خۆکار پەسند ناکرێت. پشکنەر دەبێت سەرەتا خانە زەرد و سوورەکان پێداچوونەوە و ڕاست بکاتەوە."
        }
        action={
          <span className="text-xs text-muted-foreground">
            {locale === "ar" ? "تدريب أقل من 30 دقيقة" : "ڕاهێنان کەمتر لە ٣٠ خولەک"}
          </span>
        }
      />

      <AuditorOnboarding locale={locale} force />

      {done && (
        <div className="mb-4 p-4 rounded-lg bg-success/10 border border-success/30 text-success font-bold">
          {CERTIFIED_AND_NEXT[locale]}
        </div>
      )}
      {!current ? (
        <div className="p-6 rounded-xl bg-card border border-border">{NO_PENDING[locale]}</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl bg-card border border-border overflow-hidden">
            <div className="px-4 py-3 border-b border-border flex items-center gap-2 bg-secondary">
              <FileText className="w-4 h-4" />
              <span className="text-sm font-medium">{current.filename}</span>
            </div>
            <img src={current.imageUrl} alt="invoice" className="w-full h-[560px] object-cover" />
          </div>
          <div className="rounded-xl bg-card border border-border p-6 space-y-4">
            <h3 className="font-bold border-b border-border pb-3">
              {locale === "ar" ? "الحقول المستخرجة مع الثقة" : "خانە دەرهێنراوەکان لەگەڵ متمانە"}
            </h3>
            {fields.map((f, i) => {
              const { tone, Icon, label } = flagFor(f.confidence, locale);
              const toneClass: Record<string, string> = {
                success: "border-success/40 text-success",
                warning: "border-warning/40 text-warning",
                danger: "border-danger/40 text-danger",
              };
              return (
                <div key={f.key}>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium">{f.label}</label>
                    <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border ${toneClass[tone]}`}>
                      <Icon className="w-3 h-3" /> {label} ({f.confidence}%)
                    </span>
                  </div>
                  <input
                    value={String(f.value)}
                    onChange={(e) =>
                      setFields(fields.map((x, idx) => (idx === i ? { ...x, value: e.target.value } : x)))
                    }
                    className={`w-full px-3 py-2 rounded-md bg-background border ${toneClass[tone]}`}
                    dir="ltr"
                  />
                </div>
              );
            })}
            <button
              disabled={unresolved}
              onClick={certify}
              className="w-full py-3 rounded-md bg-primary text-primary-foreground font-bold hover:opacity-90 transition mt-4 disabled:opacity-50"
            >
              {CERTIFY_BUTTON[locale]}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
