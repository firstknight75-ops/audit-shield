import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { formatIQD, wasteByDepartment } from "@/lib/mock-data";

export const Route = createFileRoute("/gm/")({
  component: () => (
    <div>
      <PageHeader title="لوحة المدير العام" subtitle="نسخة تشغيلية موسّعة من لوحة المالك (بدون محاكي القرار والتصدير الكامل)" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {wasteByDepartment.map((d) => (
          <div key={d.name} className="p-5 rounded-xl bg-card border border-border flex items-center justify-between">
            <div>
              <div className="font-bold">{d.name}</div>
              <div className="text-xs text-muted-foreground mt-1">هدر مرصود هذا الشهر</div>
            </div>
            <div className="text-lg font-bold text-warning">{formatIQD(d.value)}</div>
          </div>
        ))}
      </div>
    </div>
  ),
});