import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { Sparkles, Plus } from "lucide-react";

const presets = [
  { name: "التصنيع", criteria: ["OEE", "نسبة التلف", "زمن التوقف"] },
  { name: "المطاعم", criteria: ["تكلفة الطعام", "دوران الطاولات", "نسبة الهدر"] },
  { name: "العقارات", criteria: ["العائد الإيجاري", "نسبة الشغور", "هامش الصيانة"] },
  { name: "التجارة", criteria: ["دوران المخزون", "هامش الربح", "متوسط الفاتورة"] },
];

export const Route = createFileRoute("/appowner/templates")({
  component: () => (
    <div>
      <PageHeader
        title="محرر القوالب القطاعية"
        subtitle="إنشاء قوالب تحليل بدون كود — تُدفع لكل عميل عبر نفق VPN مشفّر"
        action={
          <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold">
            <Plus className="w-4 h-4" /> قالب جديد
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {presets.map((p) => (
          <div key={p.name} className="p-5 rounded-xl bg-card border border-border">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-primary" />
              <div className="font-bold">قطاع {p.name}</div>
            </div>
            <div className="text-xs text-muted-foreground mb-3">معايير محسوبة تلقائياً:</div>
            <div className="flex flex-wrap gap-1.5">
              {p.criteria.map((c) => (
                <span key={c} className="text-xs px-2 py-1 rounded-md bg-secondary border border-border">{c}</span>
              ))}
            </div>
            <div className="flex gap-2 mt-4 pt-3 border-t border-border">
              <button className="text-xs text-primary hover:underline">تحرير</button>
              <button className="text-xs text-primary hover:underline">دفع التحديث للعملاء</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  ),
});