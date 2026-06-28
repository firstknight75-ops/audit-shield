import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { sampleInvoice } from "@/lib/mock-data";
import { CheckCircle2, AlertCircle, XCircle, FileText } from "lucide-react";

export const Route = createFileRoute("/auditor/")({ component: AuditorCert });

function flagFor(conf: number) {
  if (conf >= 85) return { tone: "success", Icon: CheckCircle2, label: "أخضر" };
  if (conf >= 60) return { tone: "warning", Icon: AlertCircle, label: "أصفر" };
  return { tone: "danger", Icon: XCircle, label: "أحمر" };
}

function AuditorCert() {
  const [fields, setFields] = useState(sampleInvoice.fields);
  const [done, setDone] = useState(false);
  const unresolved = fields.some((f) => f.confidence < 85 && String(f.value).trim() === "");

  return (
    <div>
      <PageHeader title="منصة اعتماد المستندات" subtitle="عرض ثنائي: الأصل على اليسار والحقول على اليمين. لا اعتماد بدون تصحيح كل الحقول الصفراء والحمراء." action={<span className="text-xs text-muted-foreground">وقت التدريب المستهدف أقل من 30 دقيقة</span>} />
      {done && <div className="mb-4 p-4 rounded-lg bg-success/10 border border-success/30 text-success font-bold">تم اعتماد المستند وإضافة قيد هاش إلى السجل. جاري تحميل المستند التالي...</div>}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl bg-card border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center gap-2 bg-secondary"><FileText className="w-4 h-4" /><span className="text-sm font-medium">{sampleInvoice.filename}</span></div>
          <img src={sampleInvoice.imageUrl} alt="invoice" className="w-full h-[560px] object-cover" />
        </div>
        <div className="rounded-xl bg-card border border-border p-6 space-y-4">
          <h3 className="font-bold border-b border-border pb-3">الحقول المستخرجة مع الثقة</h3>
          {fields.map((f, i) => {
            const { tone, Icon, label } = flagFor(f.confidence);
            const toneClass: Record<string, string> = { success: "border-success/40 text-success", warning: "border-warning/40 text-warning", danger: "border-danger/40 text-danger" };
            return <div key={f.key}><div className="flex items-center justify-between mb-1"><label className="text-sm font-medium">{f.label}</label><span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border ${toneClass[tone]}`}><Icon className="w-3 h-3" /> {label} ({f.confidence}%)</span></div><input value={String(f.value)} onChange={(e) => setFields(fields.map((x, idx) => idx === i ? { ...x, value: e.target.value } : x))} className={`w-full px-3 py-2 rounded-md bg-background border ${toneClass[tone]}`} dir="ltr" /></div>;
          })}
          <button disabled={unresolved} onClick={() => { setDone(true); setTimeout(() => setDone(false), 2500); }} className="w-full py-3 rounded-md bg-primary text-primary-foreground font-bold hover:opacity-90 transition mt-4 disabled:opacity-50">تأكيد واعتماد المستند</button>
        </div>
      </div>
    </div>
  );
}
