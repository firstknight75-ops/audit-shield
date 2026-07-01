import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { FileText, ShieldCheck, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/owner/layer4")({ component: Layer4 });

// Layer 4 drill-down — original invoice image.
// Per AuditCore principle 5: 4-layer drill-down from executive summary
// to the original invoice image.
const trace = {
  document_id: "doc-001",
  filename: "invoice-INV-2026-9001.pdf",
  uploaded_at: "2026-06-27 14:32",
  certified_at: "2026-06-27 16:48",
  certified_by: "ژمێریار — زينب الكاظمي",
  extracted: {
    invoice_number: "INV-2026-9001",
    date: "2026-06-28",
    amount: "12,450,000",
    vendor_name: "شركة الرافدين",
    items_list: ["صنف 1", "صنف 2"],
  },
  ledger: [
    { action: "document.uploaded", at: "2026-06-27 14:32" },
    { action: "ocr.extracted", at: "2026-06-27 14:35" },
    { action: "certification.certified", at: "2026-06-27 16:48" },
    { action: "analytics.linked", at: "2026-06-28 02:00" },
    { action: "waste_map.flagged (duplicate_invoice)", at: "2026-06-28 02:00" },
  ],
};

function Layer4() {
  return (
    <div>
      <PageHeader
        title="الطبقة الرابعة: المستند الأصلي"
        subtitle="الحفر العميق من الملخص التنفيذي إلى الفاتورة الأصلية — مع سلسلة السجل."
        action={
          <button className="flex items-center gap-2 px-3 py-2 rounded-md bg-primary text-primary-foreground text-sm">
            <FileText className="w-4 h-4" /> تحميل الأصل
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl bg-card border border-border">
          <div className="aspect-[3/4] bg-secondary rounded-lg flex flex-col items-center justify-center text-center p-8">
            <FileText className="w-16 h-16 text-muted-foreground mb-4" />
            <div className="font-mono text-sm">{trace.filename}</div>
            <div className="text-xs text-muted-foreground mt-2">
              الصورة الأصلية معروضة هنا بعد فك التشفير في الذاكرة فقط
            </div>
          </div>
          <div className="mt-3 p-3 rounded-lg bg-primary/5 border border-primary/30 text-xs flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-primary shrink-0 mt-0.5" />
            <span>
              تم فك التشفير في الذاكرة فقط — لم يُحفظ النص الصريح على القرص. كل عملية وصول تُسجَّل
              في السجل غير القابل للتعديل.
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-card border border-border">
            <h3 className="font-bold mb-3">البيانات المعتمدة</h3>
            <dl className="space-y-2 text-sm">
              {Object.entries(trace.extracted).map(([k, v]) => (
                <div
                  key={k}
                  className="flex justify-between gap-3 border-b border-border pb-2 last:border-0 last:pb-0"
                >
                  <dt className="text-muted-foreground">{k}</dt>
                  <dd className="font-medium text-left" dir="ltr">
                    {Array.isArray(v) ? v.join("، ") : v}
                  </dd>
                </div>
              ))}
            </dl>
            <div className="mt-3 pt-3 border-t border-border text-xs text-muted-foreground">
              اعتمدها: {trace.certified_by}
              <br />
              في: {trace.certified_at}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-card border border-border">
            <h3 className="font-bold mb-3">سلسلة السجل (المصدر)</h3>
            <ol className="space-y-2 text-xs">
              {trace.ledger.map((e, i) => (
                <li key={i} className="flex items-start gap-2">
                  <ArrowRight className="w-3 h-3 text-muted-foreground shrink-0 mt-0.5" />
                  <div>
                    <div className="font-mono">{e.action}</div>
                    <div className="text-muted-foreground">{e.at}</div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
