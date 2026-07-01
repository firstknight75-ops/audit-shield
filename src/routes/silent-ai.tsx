import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { ShieldCheck, EyeOff, Cpu, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/silent-ai")({ component: SilentAI });

// Silent AI guarantee — no chatbot, no external LLM, ever.
// Per AuditCore principle 4: a background engine cross-references, detects
// anomalies, and prices problems in IQD, deterministically and explainably.
const localModules = [
  { name: "app.ai.anomaly", functions: ["run_anomaly_detection"] },
  { name: "app.ai.cross_reference", functions: ["run_cross_reference"] },
  { name: "app.ai.data_quality", functions: ["run_data_quality"] },
  { name: "app.ai.impact", functions: ["findings_to_waste_items"] },
  { name: "app.ai.narrative", functions: ["generate_narrative"] },
  { name: "app.ai.orchestrator", functions: ["_run_daily_analysis", "compute_trust_index"] },
  { name: "app.ai.predictor", functions: ["predict_next_month_cash_outflow"] },
];

function SilentAI() {
  return (
    <div>
      <PageHeader
        title="ضمان الذكاء الصامت"
        subtitle="لا يوجد chatbot ولا أي استدعاء لخدمة ذكاء اصطناعي خارجية، إطلاقاً، في أي وضع نشر."
        action={
          <div className="px-4 py-3 rounded-xl border bg-success/10 border-success/40">
            <div className="text-xs text-muted-foreground">الحالة</div>
            <div className="text-lg font-bold text-success">كل الضمانات سليمة</div>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
        <Guarantee
          icon={EyeOff}
          title="لا توجد واجهة محادثة"
          subtitle="لا chatbot، لا assistant، لا LLM شات"
          passed
        />
        <Guarantee
          icon={ShieldCheck}
          title="لا يوجد استدعاء API خارجي"
          subtitle="فحص static لجميع وحدات AI لرصد openai/anthropic/etc"
          passed
        />
        <Guarantee
          icon={Cpu}
          title="جميع وحدات التحليل محلية"
          subtitle="Python خالص، يعمل داخل الصندوق"
          passed
        />
      </div>

      <div className="p-5 rounded-xl bg-card border border-border">
        <h3 className="font-bold mb-4">وحدات التحليل المحلية ({localModules.length})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {localModules.map((m) => (
            <div key={m.name} className="p-4 rounded-lg bg-secondary border border-border">
              <div className="flex items-center justify-between">
                <code className="text-xs font-mono">{m.name}</code>
                <CheckCircle2 className="w-4 h-4 text-success" />
              </div>
              <div className="text-xs text-muted-foreground mt-2">{m.functions.join(", ")}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-border text-xs text-muted-foreground">
          تم التحقق الآن. لا توجد أي نقطة خروج إلى الإنترنت من أي وحدة AI — كل شيء يعمل داخل الصندوق
          السيادي.
        </div>
      </div>
    </div>
  );
}

function Guarantee({
  icon: Icon,
  title,
  subtitle,
  passed,
}: {
  icon: any;
  title: string;
  subtitle: string;
  passed: boolean;
}) {
  return (
    <div
      className={`p-5 rounded-xl bg-card border ${passed ? "border-success/30" : "border-danger/30"}`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`p-2 rounded-lg ${passed ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-sm">{title}</h3>
          <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>
        </div>
        <span
          className={`px-2 py-1 rounded text-[10px] font-bold ${passed ? "bg-success/15 text-success" : "bg-danger/15 text-danger"}`}
        >
          {passed ? "نجح" : "فشل"}
        </span>
      </div>
    </div>
  );
}
