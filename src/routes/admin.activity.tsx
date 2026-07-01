import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { ledgerEntries } from "@/lib/mock-data";
import { ScrollText } from "lucide-react";

export const Route = createFileRoute("/admin/activity")({
  component: () => (
    <div>
      <PageHeader
        title="سجل النشاط"
        subtitle="منح/سحب الصلاحيات وإجراءات المستخدمين — مأخوذة من السجل"
      />
      <div className="rounded-xl bg-card border border-border divide-y divide-border">
        {ledgerEntries.map((e) => (
          <div key={e.id} className="p-4 flex items-center gap-4">
            <ScrollText className="w-5 h-5 text-primary shrink-0" />
            <div className="flex-1">
              <div className="text-sm">
                <span className="font-bold">{e.actor}</span> — {e.action}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{e.target}</div>
            </div>
            <div className="text-xs text-muted-foreground" dir="ltr">
              {e.at}
            </div>
          </div>
        ))}
      </div>
    </div>
  ),
});
