import { createFileRoute, Link } from "@tanstack/react-router";
import { ownerLayer3, formatIQD } from "@/lib/mock-data";
import { PageHeader } from "@/components/app-shell";
import { AlertTriangle } from "lucide-react";

export const Route = createFileRoute("/owner/risk-map")({ component: RiskMap });

function RiskMap() {
  return (
    <div>
      <PageHeader title="الطبقة الثالثة: نتائج التضارب والشذوذ" subtitle="عرض النتائج التي أنتجها محرك التحليل المحلي" />
      <div className="space-y-3">
        {ownerLayer3.map((r) => (
          <div key={r.id} className="p-5 rounded-xl bg-card border border-border flex items-center gap-4">
            <div className="p-3 rounded-lg border text-danger border-danger/40 bg-danger/10"><AlertTriangle className="w-5 h-5" /></div>
            <div className="flex-1">
              <div className="font-medium">{r.title}</div>
              <div className="text-xs text-muted-foreground mt-1">{r.invoice}</div>
            </div>
            <div className="font-bold text-danger">{formatIQD(r.amount)}</div>
            <Link to="/owner/what-if" className="text-xs px-3 py-2 rounded-md bg-primary text-primary-foreground">التتبع إلى الأصل</Link>
          </div>
        ))}
      </div>
    </div>
  );
}
