import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { clients } from "@/lib/mock-data";
import { CheckCircle2, AlertCircle, ShieldCheck } from "lucide-react";

export const Route = createFileRoute("/appowner/")({ component: AppOwnerClients });

const tierLabel: Record<string, string> = { essential: "أساسي", advanced: "متقدم", elite: "النخبة" };
const tierTone: Record<string, string> = {
  essential: "bg-secondary text-muted-foreground",
  advanced: "bg-primary/15 text-primary border-primary/30",
  elite: "bg-warning/15 text-warning border-warning/40",
};

function AppOwnerClients() {
  return (
    <div>
      <PageHeader
        title="الشركات العميلة"
        subtitle="مراقبة الحالة فقط — لا يمكن الاطلاع على البيانات المالية لأي شركة."
      />
      <div className="mb-4 p-3 rounded-lg bg-success/10 border border-success/30 text-success text-xs flex items-center gap-2">
        <ShieldCheck className="w-4 h-4" />
        كل البيانات تُقرأ من نقطة /health الخاصة بكل صندوق ذكي — لا اتصال مباشر بقواعد البيانات المالية.
      </div>
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary">
            <tr>
              <th className="text-right p-3">الشركة</th>
              <th className="text-right p-3">القطاع</th>
              <th className="text-right p-3">الباقة</th>
              <th className="text-right p-3">المستخدمون</th>
              <th className="text-right p-3">آخر نسخة احتياطية</th>
              <th className="text-right p-3">الحالة</th>
              <th className="text-right p-3"></th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.id} className="border-t border-border hover:bg-secondary/40">
                <td className="p-3 font-medium">{c.name}</td>
                <td className="p-3 text-muted-foreground">{c.sector}</td>
                <td className="p-3">
                  <span className={`text-xs px-2 py-1 rounded-md border ${tierTone[c.tier]}`}>{tierLabel[c.tier]}</span>
                </td>
                <td className="p-3">{c.users} / {c.cap}</td>
                <td className="p-3 text-muted-foreground">{c.lastBackup}</td>
                <td className="p-3">
                  {c.health === "ok" ? (
                    <span className="flex items-center gap-1 text-xs text-success"><CheckCircle2 className="w-3 h-3" />سليم</span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-warning"><AlertCircle className="w-3 h-3" />تحذير</span>
                  )}
                </td>
                <td className="p-3 text-left">
                  <button className="text-xs text-primary hover:underline">إدارة الباقة</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}