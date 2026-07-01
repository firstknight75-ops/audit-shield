import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileUp,
  FileCheck2,
  LayoutDashboard,
} from "lucide-react";

export const Route = createFileRoute("/owner/activation")({ component: Activation });

// 48-hour activation tracker.
// Per AuditCore principle 7: first real report within 48 hours of installation,
// tracked, not just promised.
const activation = {
  install_at: "2026-06-27 09:00",
  first_upload_at: "2026-06-27 11:24",
  first_certified_at: "2026-06-27 16:48",
  first_dashboard_at: "2026-06-28 07:30",
  elapsed_hours: 22.5,
  within_48h: true,
  completed: true,
};

const milestones = [
  {
    key: "install",
    icon: Clock,
    label: "تاريخ التركيب",
    at: activation.install_at,
    achieved: true,
  },
  {
    key: "upload",
    icon: FileUp,
    label: "أول رفع",
    at: activation.first_upload_at,
    achieved: !!activation.first_upload_at,
  },
  {
    key: "certified",
    icon: FileCheck2,
    label: "أول اعتماد",
    at: activation.first_certified_at,
    achieved: !!activation.first_certified_at,
  },
  {
    key: "dashboard",
    icon: LayoutDashboard,
    label: "أول لوحة جاهزة",
    at: activation.first_dashboard_at,
    achieved: !!activation.first_dashboard_at,
  },
];

function Activation() {
  return (
    <div>
      <PageHeader
        title="حالة التفعيل"
        subtitle="تقرير فعلي خلال 48 ساعة من التركيب — متبوع لا مجرد وعد."
        action={
          <div
            className={`px-4 py-3 rounded-xl border ${activation.within_48h ? "bg-success/10 border-success/40" : "bg-warning/10 border-warning/40"}`}
          >
            <div className="text-xs text-muted-foreground">المؤشر</div>
            <div
              className={`text-lg font-bold ${activation.within_48h ? "text-success" : "text-warning"}`}
            >
              {activation.within_48h ? "تم التفعيل خلال 48 ساعة" : "تجاوز وقت التفعيل المستهدف"}
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1 p-8 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
          <div className="text-6xl font-bold text-primary">{activation.elapsed_hours}</div>
          <div className="text-sm text-muted-foreground mt-2">ساعات من التركيب</div>
          <div className="text-xs text-muted-foreground mt-1">الهدف: ≤ 48 ساعة</div>
        </div>

        <div className="lg:col-span-2 space-y-3">
          {milestones.map((m, i) => {
            const Icon = m.icon;
            return (
              <div
                key={m.key}
                className={`p-4 rounded-xl bg-card border ${m.achieved ? "border-success/30" : "border-border"} flex items-center gap-4`}
              >
                <div
                  className={`p-2 rounded-lg ${m.achieved ? "bg-success/10 text-success" : "bg-secondary text-muted-foreground"}`}
                >
                  {m.achieved ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <AlertTriangle className="w-5 h-5" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{m.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">{m.at || "لم يكتمل بعد"}</div>
                </div>
                <Icon className="w-4 h-4 text-muted-foreground" />
              </div>
            );
          })}
        </div>
      </div>

      <div className="p-5 rounded-xl bg-primary/5 border border-primary/30 text-sm leading-relaxed">
        <strong>كيف نحسب:</strong> نقيس عدد الساعات بين{" "}
        <code className="bg-secondary px-1 rounded">CompanyGroup.created_at</code> وأول لوحة تنفيذية
        جاهزة (<code className="bg-secondary px-1 rounded">AnalyticsOutput.created_at</code>). كل
        فحص يُسجَّل في السجل غير القابل للتعديل.
      </div>
    </div>
  );
}
