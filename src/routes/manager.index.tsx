import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { managerWidgets } from "@/lib/mock-data";

export const Route = createFileRoute("/manager/")({ component: ManagerHome });

function ManagerHome() {
  return (
    <div>
      <PageHeader title="لوحة المدير" subtitle="شبكة Widgets قابلة لإعادة الترتيب ضمن نطاق القسم/الفرع فقط" />
      <div className="mb-4 p-3 rounded-lg bg-primary/10 border border-primary/30 text-primary text-xs">السحب والإفلات هنا تمثيلي في هذه النسخة، مع بقاء نطاق البيانات مقيداً على الخادم.</div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {managerWidgets.map((w) => (
          <div key={w.code} className="p-5 rounded-xl bg-card border border-border cursor-move hover:border-primary transition">
            <div className="text-xs text-muted-foreground">{w.code}</div>
            <div className="font-bold mt-2">{w.title}</div>
            <div className="text-2xl mt-3">{w.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
