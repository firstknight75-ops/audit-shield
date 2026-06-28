import { createFileRoute } from "@tanstack/react-router";
import { wasteByDepartment, formatIQD } from "@/lib/mock-data";
import { PageHeader } from "@/components/app-shell";
import { TrendingDown } from "lucide-react";

export const Route = createFileRoute("/owner/waste-map")({ component: WasteMap });

const items = [
  { id: 1, desc: "فاتورة مكررة — مورد الرافدين", dept: "المشتريات", amount: 12_400_000, status: "مفتوح" },
  { id: 2, desc: "تباين في كميات المخزن — 8 أصناف", dept: "المخازن", amount: 6_800_000, status: "قيد المراجعة" },
  { id: 3, desc: "صرف نقدي بدون مستند", dept: "المالية", amount: 3_200_000, status: "مفتوح" },
  { id: 4, desc: "خصومات غير معتمدة", dept: "المبيعات", amount: 4_500_000, status: "مفتوح" },
  { id: 5, desc: "زيادة شاذة في مصاريف الوقود", dept: "النقل", amount: 1_900_000, status: "مفتوح" },
];

function WasteMap() {
  const total = items.reduce((s, i) => s + i.amount, 0);
  return (
    <div>
      <PageHeader
        title="خريطة الهدر"
        subtitle="كل بند مسعّر بالدينار العراقي ومرتبط بمستند أصلي قابل للتتبع"
        action={
          <div className="text-right">
            <div className="text-xs text-muted-foreground">إجمالي الهدر المرصود</div>
            <div className="text-xl font-bold text-danger">{formatIQD(total)}</div>
          </div>
        }
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {items.map((i) => (
          <div key={i.id} className="p-5 rounded-xl bg-card border border-border hover:border-danger/50 transition">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-danger/10 text-danger border border-danger/30">
                  <TrendingDown className="w-4 h-4" />
                </div>
                <span className="text-xs px-2 py-1 rounded-md bg-secondary">{i.dept}</span>
              </div>
              <span className="text-xs text-muted-foreground">{i.status}</span>
            </div>
            <div className="mt-3 font-medium leading-relaxed">{i.desc}</div>
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <div className="text-lg font-bold text-danger">{formatIQD(i.amount)}</div>
              <button className="text-xs text-primary hover:underline">عرض المستند الأصلي ←</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}