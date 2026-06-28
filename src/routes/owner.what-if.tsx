import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { ownerLayer4 } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/what-if")({ component: Layer4 });

function Layer4() {
  return (
    <div>
      <PageHeader title="الطبقة الرابعة: المستند الأصلي + أثر السجل" subtitle="النزول من المؤشر التنفيذي إلى صورة الفاتورة نفسها مع السلسلة الكاملة" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl bg-card border border-border overflow-hidden">
          <img src={ownerLayer4.imageUrl} alt="document" className="w-full h-[560px] object-cover" />
        </div>
        <div className="rounded-xl bg-card border border-border p-6">
          <div className="font-bold mb-3">{ownerLayer4.filename}</div>
          <div className="space-y-3">
            {ownerLayer4.ledger.map((l) => (
              <div key={l.id} className="p-3 rounded-md bg-secondary flex items-center justify-between">
                <span>{l.action}</span>
                <span className="text-xs text-muted-foreground" dir="ltr">{l.at}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
