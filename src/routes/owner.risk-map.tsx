import { createFileRoute } from "@tanstack/react-router";
import { riskAlerts, formatIQD } from "@/lib/mock-data";
import { PageHeader } from "@/components/app-shell";
import { AlertTriangle } from "lucide-react";

export const Route = createFileRoute("/owner/risk-map")({ component: RiskMap });

const sevTone: Record<string, string> = {
  critical: "text-danger border-danger/40 bg-danger/10",
  high: "text-warning border-warning/40 bg-warning/10",
  medium: "text-primary border-primary/40 bg-primary/10",
};
const sevLabel: Record<string, string> = { critical: "حرج", high: "مرتفع", medium: "متوسط" };

function RiskMap() {
  return (
    <div>
      <PageHeader title="خريطة المخاطر" subtitle="التهديدات مرتّبة حسب الأولوية والأثر المالي" />
      <div className="space-y-3">
        {riskAlerts.map((r) => (
          <div key={r.id} className="p-5 rounded-xl bg-card border border-border flex items-center gap-4">
            <div className={`p-3 rounded-lg border ${sevTone[r.severity]}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs px-2 py-0.5 rounded-md border ${sevTone[r.severity]}`}>{sevLabel[r.severity]}</span>
                <span className="text-xs text-muted-foreground">{r.department}</span>
              </div>
              <div className="font-medium">{r.title}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground">الأثر</div>
              <div className="font-bold text-danger">{r.impact ? formatIQD(r.impact) : "—"}</div>
            </div>
            <button className="text-xs px-3 py-2 rounded-md bg-primary text-primary-foreground hover:opacity-90">معالجة</button>
          </div>
        ))}
      </div>
    </div>
  );
}