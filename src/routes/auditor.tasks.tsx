import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { auditorTasks } from "@/lib/mock-data";

export const Route = createFileRoute("/auditor/tasks")({ component: Tasks });

function Tasks() {
  const done = auditorTasks.filter(t => t.status === "done").length;
  const overdue = auditorTasks.filter(t => t.status === "overdue").length;
  const demerits = auditorTasks.reduce((s, t) => s + t.demerits, 0);

  return (
    <div>
      <PageHeader
        title="مهامي اليومية"
        subtitle={`المهام المنجزة: ${done} | المتأخرة: ${overdue} | النقاط السلبية: ${demerits}`}
      />
      <div className="space-y-3">
        {auditorTasks.map((t) => {
          const overdueRow = t.status === "overdue";
          return (
            <div key={t.id} className={`p-4 rounded-xl bg-card border ${overdueRow ? "border-danger/40" : "border-border"} flex items-center justify-between`}>
              <div className="flex items-center gap-4">
                <div className={`w-2 h-12 rounded-full ${overdueRow ? "bg-danger" : t.remaining < 120 ? "bg-warning" : "bg-success"}`} />
                <div>
                  <div className="font-medium">{t.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">{t.type} · موعد التسليم: {t.sla}</div>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-sm font-bold ${overdueRow ? "text-danger" : "text-foreground"}`}>
                  {overdueRow ? `متأخر ${Math.abs(t.remaining)} د` : `متبقي ${t.remaining} د`}
                </div>
                {t.demerits > 0 && <div className="text-xs text-danger mt-1">+{t.demerits} نقاط سلبية</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}