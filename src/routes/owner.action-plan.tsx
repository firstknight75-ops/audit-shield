import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { Wrench, Layers, Calendar, User as UserIcon } from "lucide-react";
import { formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/action-plan")({ component: ActionPlan });

// Action Plan — two distinct paths:
//   Change path     = prioritized items to fix NOW (from waste map, by IQD impact)
//   Adaptation path = structural recommendations based on actual data patterns
const changePath = [
  { id: 1, title: "معالجة: فاتورة مكررة — شركة الرافدين", rationale: "اكتُشف بند بقيمة 12,400,000 د.ع", priority: 1, deadline_days: 14, estimated_iqd: 12_400_000, owner_role: "مدير قسم" },
  { id: 2, title: "معالجة: تباين في كميات المخزن — 8 أصناف", rationale: "اكتُشف بند بقيمة 6,800,000 د.ع", priority: 2, deadline_days: 21, estimated_iqd: 6_800_000, owner_role: "مدير قسم" },
  { id: 3, title: "معالجة: صرف نقدي بدون مستند", rationale: "اكتُشف بند بقيمة 3,200,000 د.ع", priority: 3, deadline_days: 30, estimated_iqd: 3_200_000, owner_role: "مدير قسم" },
];

const adaptationPath = [
  { id: 1, title: "إعادة جدولة عملية الاعتماد اليومية", rationale: "مؤشر الموثوقية متوسط — يستلزم تكيّف هيكلي", priority: 1, deadline_days: 21, estimated_iqd: 0, owner_role: "مدير عام" },
  { id: 2, title: "تطبيق قاعدة منع تكرار رقم الفاتورة", rationale: "رصد 2+ حالات تكرار — يستلزم ضبط هيكلي", priority: 2, deadline_days: 30, estimated_iqd: 0, owner_role: "مدير نظام" },
];

const priorityColor = (p: number) => p === 1 ? "danger" : p === 2 ? "warning" : "primary";

function ActionPlan() {
  return (
    <div>
      <PageHeader
        title="خطة العمل"
        subtitle="مسار التغيير (إصلاح فوري) ومسار التكيّف (تعديل هيكلي)."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Wrench className="w-5 h-5 text-danger" />
            <h2 className="text-lg font-bold">مسار التغيير</h2>
            <span className="text-xs text-muted-foreground">أولوية قصوى — حسب الأثر بالدينار العراقي</span>
          </div>
          <div className="space-y-3">
            {changePath.map((a) => (
              <div key={a.id} className="p-5 rounded-xl bg-card border border-border hover:border-danger/40 transition">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className={`w-7 h-7 rounded-full bg-${priorityColor(a.priority)}/15 text-${priorityColor(a.priority)} text-xs flex items-center justify-center font-bold`}>
                      {a.priority}
                    </span>
                    <span className="text-xs text-muted-foreground">أولوية {a.priority}</span>
                  </div>
                  {a.estimated_iqd > 0 && <div className="text-sm font-bold text-success">{formatIQD(a.estimated_iqd)}</div>}
                </div>
                <div className="mt-3 font-medium leading-relaxed">{a.title}</div>
                <div className="text-xs text-muted-foreground mt-2 leading-relaxed">{a.rationale}</div>
                <div className="flex items-center gap-4 mt-4 pt-3 border-t border-border text-xs">
                  <span className="flex items-center gap-1 text-muted-foreground"><Calendar className="w-3 h-3" /> {a.deadline_days} يوم</span>
                  <span className="flex items-center gap-1 text-muted-foreground"><UserIcon className="w-3 h-3" /> {a.owner_role}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold">مسار التكيّف</h2>
            <span className="text-xs text-muted-foreground">تعديلات هيكلية — أثرها متوسط إلى طويل المدى</span>
          </div>
          <div className="space-y-3">
            {adaptationPath.map((a) => (
              <div key={a.id} className="p-5 rounded-xl bg-card border border-border hover:border-primary/40 transition">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className={`w-7 h-7 rounded-full bg-${priorityColor(a.priority)}/15 text-${priorityColor(a.priority)} text-xs flex items-center justify-center font-bold`}>
                      {a.priority}
                    </span>
                    <span className="text-xs text-muted-foreground">أولوية {a.priority}</span>
                  </div>
                </div>
                <div className="mt-3 font-medium leading-relaxed">{a.title}</div>
                <div className="text-xs text-muted-foreground mt-2 leading-relaxed">{a.rationale}</div>
                <div className="flex items-center gap-4 mt-4 pt-3 border-t border-border text-xs">
                  <span className="flex items-center gap-1 text-muted-foreground"><Calendar className="w-3 h-3" /> {a.deadline_days} يوم</span>
                  <span className="flex items-center gap-1 text-muted-foreground"><UserIcon className="w-3 h-3" /> {a.owner_role}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
