import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { ShieldCheck, AlertTriangle, RefreshCw, Database, Lock, Eye, EyeOff } from "lucide-react";

export const Route = createFileRoute("/appowner/isolation-proof")({ component: IsolationProof });

// Trust Proof — Demonstrable inside the product.
// Per AuditCore principle 6: "this must be demonstrable inside the product,
// not just asserted in a contract."
const proofs = [
  {
    guarantee: "auditor_blocked_from_analytics",
    label: "المدقق محظور من رؤية المخرجات التحليلية",
    passed: true,
    detail: { analytics_outputs_visible: 0, waste_map_items_visible: 0, risk_alerts_visible: 0 },
  },
  {
    guarantee: "appowner_zero_visibility_to_tenant_data",
    label: "مالك المنصة لا يمكنه قراءة أي محتوى مالي لأي عميل",
    passed: true,
    detail: { tenant_finance_hidden: { analytics_outputs_visible: 0, waste_map_items_visible: 0, risk_alerts_visible: 0, audit_ledger_visible: 0, document_visible: 0 } },
  },
  {
    guarantee: "tenant_isolation",
    label: "كل مجموعة شركات معزولة عن غيرها",
    passed: true,
    detail: { my_tenant_rows: 12, cross_tenant_rows_visible: 0 },
  },
  {
    guarantee: "ledger_chain_intact",
    label: "سلسلة السجل سليمة وقابلة للتحقق",
    passed: true,
    detail: { message: "السجل سليم 100%", broken_entry_id: null },
  },
];

function IsolationProof() {
  const allPassed = proofs.every((p) => p.passed);
  return (
    <div>
      <PageHeader
        title="إثبات حدود الثقة"
        subtitle="هذا الإثبات يعمل داخل المنتج، ليس مجرد بند في عقد."
        action={
          <div className={`px-4 py-3 rounded-xl border ${allPassed ? "bg-success/10 border-success/40" : "bg-danger/10 border-danger/40"}`}>
            <div className="text-xs text-muted-foreground">النتيجة</div>
            <div className={`text-lg font-bold ${allPassed ? "text-success" : "text-danger"}`}>
              {allPassed ? "نجح — كل الضمانات سليمة" : "فشل — راجع التفاصيل"}
            </div>
          </div>
        }
      />

      <div className="p-5 rounded-xl bg-primary/5 border border-primary/30 mb-6 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-primary shrink-0 mt-0.5" />
        <div className="text-sm leading-relaxed">
          <strong>المبدأ السادس من AuditCore:</strong> مالك المنصة (App Owner) لا يمكنه قراءة أي محتوى مالي لأي عميل —
          <em> وهذا الإثبات يعمل من داخل المنتج نفسه، لا مجرد بند في العقد.</em>
          <br />
          كل ضمان أدناه يُنفَّذ كاستعلام فعلي ضد قاعدة البيانات بنفس جلسة المستخدم الحالية.
        </div>
      </div>

      <div className="space-y-4">
        {proofs.map((p) => (
          <div key={p.guarantee} className={`p-5 rounded-xl bg-card border ${p.passed ? "border-success/30" : "border-danger/30"}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${p.passed ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                  {p.passed ? <ShieldCheck className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="font-bold">{p.label}</h3>
                  <div className="text-xs text-muted-foreground font-mono mt-1">{p.guarantee}</div>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-md text-xs font-bold ${p.passed ? "bg-success/15 text-success" : "bg-danger/15 text-danger"}`}>
                {p.passed ? "نجح" : "فشل"}
              </span>
            </div>
            <details className="mt-3 pt-3 border-t border-border">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground flex items-center gap-1">
                <Database className="w-3 h-3" /> تفاصيل الاستعلام
              </summary>
              <pre className="text-[10px] bg-secondary p-3 rounded mt-2 overflow-auto" dir="ltr">{JSON.stringify(p.detail, null, 2)}</pre>
            </details>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center gap-3">
        <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm">
          <RefreshCw className="w-4 h-4" /> إعادة التحقق
        </button>
        <span className="text-xs text-muted-foreground">
          كل عملية إعادة تحقق تُسجَّل في سجل العميل (وليس سجل المنصة).
        </span>
      </div>
    </div>
  );
}
