import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { ShieldCheck, TrendingUp, FileCheck2, AlertTriangle, Layers } from "lucide-react";

export const Route = createFileRoute("/owner/trust-index")({ component: TrustIndex });

// Standalone Trust Index — first-class deliverable, not a dashboard card.
// Per AuditCore output #2: مؤشر الموثوقية.
const trust = {
  score: 78,
  level: "high" as "high" | "medium" | "low",
  coverage_pct: 92.4,
  certified_pct: 84.0,
  duplicate_pct: 3.2,
  missing_field_pct: 7.6,
  total_documents: 312,
  certified_documents: 262,
  duplicate_documents: 10,
  missing_fields_total: 95,
  last_run: "2026-06-29 08:00",
};

const levelMeta = {
  high: { label: "موثوقية عالية", color: "success", ring: "border-success/40" },
  medium: { label: "موثوقية متوسطة", color: "warning", ring: "border-warning/40" },
  low: { label: "موثوقية منخفضة", color: "danger", ring: "border-danger/40" },
};

function TrustIndex() {
  const meta = levelMeta[trust.level];
  return (
    <div>
      <PageHeader
        title="مؤشر الموثوقية"
        subtitle="مقياس مستقل لجودة البيانات والتغطية — ليس مجرد بطاقة في لوحة."
        action={
          <div className={`px-4 py-3 rounded-xl border bg-${meta.color}/10 ${meta.ring}`}>
            <div className="text-xs text-muted-foreground">المستوى</div>
            <div className={`text-lg font-bold text-${meta.color}`}>{meta.label}</div>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1 p-8 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
          <div className="relative w-44 h-44">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              <circle cx="50" cy="50" r="42" fill="none" stroke="oklch(0.32 0.03 250)" strokeWidth="10" />
              <circle
                cx="50" cy="50" r="42" fill="none"
                stroke={`oklch(var(--${meta.color}))`}
                strokeWidth="10"
                strokeDasharray={`${(trust.score / 100) * 264} 264`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-4xl font-bold">{trust.score}</div>
              <div className="text-xs text-muted-foreground">من 100</div>
            </div>
          </div>
          <div className="text-sm text-muted-foreground mt-3">آخر تشغيل: {trust.last_run}</div>
        </div>

        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <Component label="التغطية" value={`${trust.coverage_pct}%`} icon={Layers} tone="primary" />
          <Component label="مستندات معتمدة" value={`${trust.certified_pct}%`} sub={`${trust.certified_documents} / ${trust.total_documents}`} icon={FileCheck2} tone="success" />
          <Component label="حقول مفقودة" value={`${trust.missing_field_pct}%`} sub={`${trust.missing_fields_total} حقل`} icon={AlertTriangle} tone="warning" />
          <Component label="مستندات مكررة" value={`${trust.duplicate_pct}%`} sub={`${trust.duplicate_documents} مستند`} icon={TrendingUp} tone="danger" />
        </div>
      </div>

      <div className="p-5 rounded-xl bg-card border border-border">
        <h3 className="font-bold mb-3 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-primary" /> كيف يُحسب المؤشر</h3>
        <ul className="space-y-2 text-sm text-muted-foreground leading-relaxed">
          <li>• <strong className="text-foreground">التغطية (35%)</strong> — نسبة المستندات التي تحوي جميع الحقول الأربعة المطلوبة (رقم الفاتورة، التاريخ، المبلغ، المورّد).</li>
          <li>• <strong className="text-foreground">الاعتماد (30%)</strong> — نسبة المستندات التي اعتمدها المدقق بعد التصحيح البشري.</li>
          <li>• <strong className="text-foreground">اكتمال الحقول (20%)</strong> — مقلوب نسبة الحقول المفقودة.</li>
          <li>• <strong className="text-foreground">عدم التكرار (15%)</strong> — مقلوب نسبة المستندات المكررة.</li>
        </ul>
        <div className="mt-4 pt-4 border-t border-border text-xs text-muted-foreground">
          كل فحص يُسجَّل في السجل غير القابل للتعديل (ledger) لأغرام الرجوع والمراجعة.
        </div>
      </div>
    </div>
  );
}

function Component({ label, value, sub, icon: Icon, tone }: { label: string; value: string; sub?: string; icon: any; tone: string }) {
  return (
    <div className={`p-5 rounded-xl bg-card border border-border border-${tone}/30`}>
      <div className="flex items-center gap-2 mb-3">
        <div className={`p-2 rounded-lg bg-${tone}/10 text-${tone}`}><Icon className="w-4 h-4" /></div>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className={`text-2xl font-bold text-${tone}`}>{value}</div>
      {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
    </div>
  );
}
