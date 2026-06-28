import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
export const Route = createFileRoute("/manager/tasks")({
  component: () => (
    <div>
      <PageHeader title="مهام التصحيح" subtitle="مهام تخص قسمك فقط" />
      <div className="p-12 rounded-xl bg-card border border-border text-center text-muted-foreground">
        لا توجد مهام تصحيح مفتوحة حالياً.
      </div>
    </div>
  ),
});