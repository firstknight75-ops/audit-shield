import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
export const Route = createFileRoute("/gm/departments")({
  component: () => (
    <div>
      <PageHeader title="أداء الأقسام" subtitle="عرض إجمالي للأقسام تحت إشرافك" />
      <div className="p-12 rounded-xl bg-card border border-border text-center text-muted-foreground">
        مخططات الأقسام التفصيلية — قيد الإعداد.
      </div>
    </div>
  ),
});