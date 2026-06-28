import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { formatIQD } from "@/lib/mock-data";
import { ClipboardList, AlertCircle, TrendingUp, Gauge } from "lucide-react";

export const Route = createFileRoute("/manager/")({ component: ManagerHome });

function ManagerHome() {
  return (
    <div>
      <PageHeader title="لوحة قسم المشتريات" subtitle="نطاقك: قسم المشتريات — فرع بغداد الرئيسي فقط" />
      <div className="mb-4 p-3 rounded-lg bg-primary/10 border border-primary/30 text-primary text-xs">
        ⓘ هذه اللوحة تعرض بيانات قسمك حصراً. لا يمكنك الوصول لبيانات الأقسام الأخرى.
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Widget icon={ClipboardList} label="مهام تصحيح مفتوحة" value="6" tone="primary" />
        <Widget icon={AlertCircle} label="مؤشر جودة بيانات القسم" value="87 / 100" tone="success" />
        <Widget icon={TrendingUp} label="أداء الميزانية" value="+12%" tone="success" />
        <Widget icon={Gauge} label="SLA مهدد" value="2 مهمة" tone="warning" />
      </div>
      <div className="p-6 rounded-xl bg-card border border-border">
        <h3 className="font-bold mb-4">مهام مؤثرة على SLA</h3>
        <div className="space-y-2">
          {[
            { t: "اعتماد مورد جديد — شركة العاني", impact: 8_500_000 },
            { t: "مراجعة عقد الإمداد الشهري", impact: 22_000_000 },
          ].map((x, i) => (
            <div key={i} className="p-3 rounded-md bg-secondary flex items-center justify-between text-sm">
              <span>{x.t}</span>
              <span className="text-warning font-bold">{formatIQD(x.impact)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Widget({ icon: Icon, label, value, tone }: any) {
  const t: Record<string, string> = {
    primary: "text-primary border-primary/30",
    success: "text-success border-success/30",
    warning: "text-warning border-warning/30",
  };
  return (
    <div className="p-4 rounded-xl bg-card border border-border">
      <div className={`inline-flex p-2 rounded-lg border ${t[tone]}`}><Icon className="w-4 h-4" /></div>
      <div className="text-xs text-muted-foreground mt-3">{label}</div>
      <div className="text-xl font-bold mt-1">{value}</div>
    </div>
  );
}