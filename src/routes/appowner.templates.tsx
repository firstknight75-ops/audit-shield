import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { appOwnerTemplates } from "@/lib/mock-data";

export const Route = createFileRoute("/appowner/templates")({ component: Templates });

function Templates() {
  return (
    <div>
      <PageHeader title="محرك القوالب و CRaaS" subtitle="بناء تقارير بدون كود، مع إصدار وتراجع ودفع انتقائي للعملاء" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {appOwnerTemplates.map((t) => (
          <div key={t.id} className="p-5 rounded-xl bg-card border border-border">
            <div className="font-bold">{t.name}</div>
            <div className="text-sm text-muted-foreground mt-1">{t.sector} · v{t.version}</div>
            <div className="mt-4 flex gap-3 text-xs text-primary">
              <button>تحرير</button>
              <button>Rollback</button>
              <button>Push Update</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
