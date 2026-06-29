import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { Briefcase, ShieldCheck, AlertTriangle, TrendingDown, Sparkles } from "lucide-react";
import { formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/portfolio")({ component: Portfolio });

// Portfolio view — multi-company owner view, never silently blended.
const companies = [
  { company_id: "c1", company_name: "شركة الفرات للتجارة", trust_index_score: 80, monthly_waste_iqd: 1_500_000, critical_alerts: 2, opportunity_iqd: 4_500_000, risk_alerts: 5, documents_total: 220 },
  { company_id: "c2", company_name: "مصنع الفرات للصناعات", trust_index_score: 65, monthly_waste_iqd: 3_200_000, critical_alerts: 4, opportunity_iqd: 1_800_000, risk_alerts: 9, documents_total: 180 },
];

const totals = {
  monthly_waste_iqd: companies.reduce((s, c) => s + c.monthly_waste_iqd, 0),
  opportunity_iqd: companies.reduce((s, c) => s + c.opportunity_iqd, 0),
  risk_alerts: companies.reduce((s, c) => s + c.risk_alerts, 0),
  documents_total: companies.reduce((s, c) => s + c.documents_total, 0),
};

function Portfolio() {
  return (
    <div>
      <PageHeader
        title="محفظة الشركات"
        subtitle="كل شركة تُعرض على حدة — الأرقام لا تُمزج بصمت."
      />

      <div className="space-y-4 mb-8">
        {companies.map((c) => (
          <div key={c.company_id} className="p-6 rounded-xl bg-card border border-border">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-primary/10 text-primary border border-primary/30">
                  <Briefcase className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold">{c.company_name}</h3>
                  <div className="text-xs text-muted-foreground mt-1">ID: {c.company_id}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground">مؤشر الموثوقية</div>
                <div className={`text-2xl font-bold ${c.trust_index_score >= 80 ? "text-success" : c.trust_index_score >= 60 ? "text-warning" : "text-danger"}`}>
                  {c.trust_index_score}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-border">
              <Stat icon={TrendingDown} label="الهدر" value={formatIQD(c.monthly_waste_iqd)} tone="danger" />
              <Stat icon={AlertTriangle} label="المخاطر" value={String(c.risk_alerts)} sub={`${c.critical_alerts} حرجة`} tone="warning" />
              <Stat icon={Sparkles} label="الفرص" value={formatIQD(c.opportunity_iqd)} tone="success" />
              <Stat icon={ShieldCheck} label="المستندات" value={String(c.documents_total)} tone="primary" />
            </div>
          </div>
        ))}
      </div>

      <div className="p-5 rounded-xl bg-warning/5 border border-warning/30 mb-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
          <div className="text-sm leading-relaxed">
            <strong>هذه أرقام منفصلة لكل شركة. لا يتم دمجها تلقائياً.</strong>
            <br />
            مجموع الهدر ({formatIQD(totals.monthly_waste_iqd)}) هو مجموع حسابي صريح — وليس متوسط مرجح أو قيمة مدمجة.
          </div>
        </div>
      </div>

      <div className="p-5 rounded-xl bg-card border border-border">
        <h3 className="font-bold mb-3">المجاميع الصريحة (جمع، ليس دمج)</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><div className="text-muted-foreground">مجموع الهدر</div><div className="font-bold text-danger">{formatIQD(totals.monthly_waste_iqd)}</div></div>
          <div><div className="text-muted-foreground">مجموع الفرص</div><div className="font-bold text-success">{formatIQD(totals.opportunity_iqd)}</div></div>
          <div><div className="text-muted-foreground">مجموع التنبيهات</div><div className="font-bold text-warning">{totals.risk_alerts}</div></div>
          <div><div className="text-muted-foreground">مجموع المستندات</div><div className="font-bold text-primary">{totals.documents_total}</div></div>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, sub, tone }: { icon: any; label: string; value: string; sub?: string; tone: string }) {
  return (
    <div className={`p-3 rounded-lg bg-${tone}/5 border border-${tone}/30`}>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="w-3 h-3" /> {label}
      </div>
      <div className={`text-base font-bold text-${tone} mt-1`}>{value}</div>
      {sub && <div className="text-[10px] text-muted-foreground mt-0.5">{sub}</div>}
    </div>
  );
}
