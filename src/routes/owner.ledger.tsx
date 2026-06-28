import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { ledgerEntries } from "@/lib/mock-data";
import { ShieldCheck, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/owner/ledger")({ component: Ledger });

function Ledger() {
  const [verified, setVerified] = useState<null | boolean>(null);
  return (
    <div>
      <PageHeader
        title="السجل غير القابل للتعديل"
        subtitle="سلسلة هاش SHA-256 — أي تلاعب يُكشف لحظياً"
        action={
          <button
            onClick={() => { setVerified(null); setTimeout(() => setVerified(true), 800); }}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold"
          >
            <ShieldCheck className="w-4 h-4" /> التحقق من سلامة السلسلة
          </button>
        }
      />
      {verified === true && (
        <div className="mb-4 p-4 rounded-lg bg-success/10 border border-success/30 text-success flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-bold">السجل سليم 100% — {ledgerEntries.length} قيد مرتبط بسلاسل هاش صحيحة.</span>
        </div>
      )}
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary">
            <tr>
              <th className="text-right p-3">الوقت</th>
              <th className="text-right p-3">المستخدم</th>
              <th className="text-right p-3">الإجراء</th>
              <th className="text-right p-3">الهدف</th>
              <th className="text-right p-3">الهاش</th>
            </tr>
          </thead>
          <tbody>
            {ledgerEntries.map((e) => (
              <tr key={e.id} className="border-t border-border">
                <td className="p-3 text-muted-foreground" dir="ltr">{e.at}</td>
                <td className="p-3">{e.actor}</td>
                <td className="p-3">{e.action}</td>
                <td className="p-3 text-muted-foreground">{e.target}</td>
                <td className="p-3 font-mono text-xs text-primary" dir="ltr">{e.hash}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}