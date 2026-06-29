import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { Sparkles, TrendingUp, Building2, Clock } from "lucide-react";
import { formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/opportunity-map")({ component: OpportunityMap });

// Opportunity Map — IQD-priced upside (untapped capability).
// Distinct from Waste Map (which shows downside / leakage).
const opportunities = [
  { kind: "vendor_underutilized", description: "مورّد بحجم منخفض: شركة النور للتوريدات", iqd_amount: 2_400_000, confidence: "medium", basis: { current_iqd: 800_000, avg_iqd: 3_200_000 } },
  { kind: "branch_underutilized", description: "فرع بأداء منخفض: الفرع الثاني (البصرة)", iqd_amount: 5_100_000, confidence: "medium", basis: { current_iqd: 1_200_000, avg_iqd: 6_300_000 } },
  { kind: "timing_mismatch", description: "نافذة استرداد جزئية من غرامات التأخير", iqd_amount: 1_800_000, confidence: "low", basis: { recoverable_fraction: 0.4 } },
  { kind: "vendor_underutilized", description: "مورّد بحجم منخفض: مطبعة الأمل", iqd_amount: 950_000, confidence: "medium", basis: { current_iqd: 350_000, avg_iqd: 1_300_000 } },
];

const kindMeta = {
  vendor_underutilized: { label: "مورّد غير مستغل", icon: TrendingUp, tone: "primary" },
  branch_underutilized: { label: "فرع بأداء منخفض", icon: Building2, tone: "warning" },
  timing_mismatch: { label: "فرصة في التوقيت", icon: Clock, tone: "success" },
};

function OpportunityMap() {
  const total = opportunities.reduce((s, o) => s + o.iqd_amount, 0);
  return (
    <div>
      <PageHeader
        title="خريطة الفرص"
        subtitle="القدرة غير المستغلة، مسعّرة بالدينار العراقي."
        action={
          <div className="text-right">
            <div className="text-xs text-muted-foreground">إجمالي الفرصة بالدينار العراقي</div>
            <div className="text-2xl font-bold text-success">{formatIQD(total)}</div>
          </div>
        }
      />

      <div className="p-5 rounded-xl bg-success/5 border border-success/30 mb-6 flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-success shrink-0 mt-0.5" />
        <div className="text-sm leading-relaxed">
          <strong>هذه ليست خريطة الهدر.</strong> الهدر = ضرر/تسرّب. الفرص = قدرة غير مستغلة يمكن تحويلها إلى قيمة.
          كل بند هنا مبني على بيانات فعلية من مستندات معتمدة، مع أساس الحساب مرئي.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {opportunities.map((o, i) => {
          const meta = kindMeta[o.kind as keyof typeof kindMeta];
          const Icon = meta.icon;
          return (
            <div key={i} className="p-5 rounded-xl bg-card border border-border hover:border-success/40 transition">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-lg bg-${meta.tone}/10 text-${meta.tone} border border-${meta.tone}/30`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-md bg-${meta.tone}/15 text-${meta.tone}`}>{meta.label}</span>
                </div>
                <span className="text-xs px-2 py-1 rounded-md bg-secondary text-muted-foreground">ثقة: {o.confidence}</span>
              </div>
              <div className="mt-3 font-medium leading-relaxed">{o.description}</div>
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
                <div className="text-lg font-bold text-success">{formatIQD(o.iqd_amount)}</div>
                <button className="text-xs text-primary hover:underline">عرض الأساس الحسابي ←</button>
              </div>
              <details className="mt-2">
                <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">الأساس الحسابي</summary>
                <pre className="text-[10px] bg-secondary p-2 rounded mt-2 overflow-auto" dir="ltr">{JSON.stringify(o.basis, null, 2)}</pre>
              </details>
            </div>
          );
        })}
      </div>
    </div>
  );
}
