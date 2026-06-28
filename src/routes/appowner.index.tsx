import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { clients } from "@/lib/mock-data";

export const Route = createFileRoute("/appowner/")({ component: AppOwnerClients });

function AppOwnerClients() {
  return (
    <div>
      <PageHeader title="مركز قيادة App Owner" subtitle="جرد العملاء عبر السحابة والصناديق الذكية دون لمس المخططات المالية للعملاء" />
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary"><tr><th className="text-right p-3">الشركة</th><th className="text-right p-3">النمط</th><th className="text-right p-3">الباقة</th><th className="text-right p-3">المستخدمون</th><th className="text-right p-3">الصحة</th><th className="text-right p-3">النسخ الاحتياطي</th></tr></thead>
          <tbody>{clients.map((c) => <tr key={c.id} className="border-t border-border"><td className="p-3">{c.name}</td><td className="p-3">{c.id === 'c1' ? 'cloud' : 'onpremise'}</td><td className="p-3">{c.tier}</td><td className="p-3">{c.users}/{c.cap}</td><td className="p-3">{c.health}</td><td className="p-3">{c.lastBackup}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
