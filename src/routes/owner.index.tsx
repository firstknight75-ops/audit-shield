import { createFileRoute, Link } from "@tanstack/react-router";
import { ownerKpis, cashTrend, formatIQD } from "@/lib/mock-data";
import { PageHeader } from "@/components/app-shell";
import { TrendingDown, ShieldCheck, AlertTriangle, Wallet, Users, ArrowLeft } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export const Route = createFileRoute("/owner/")({
  component: OwnerHome,
});

const cards = [
  { key: "waste", label: "إجمالي الهدر الشهري", value: formatIQD(ownerKpis.monthlyWaste), icon: TrendingDown, tone: "danger", to: "/owner/waste-map" },
  { key: "trust", label: "مؤشر الموثوقية", value: `${ownerKpis.trustIndex} / 100`, icon: ShieldCheck, tone: "success", to: "/owner/departments" },
  { key: "alerts", label: "تنبيهات حرجة", value: String(ownerKpis.criticalAlerts), icon: AlertTriangle, tone: "warning", to: "/owner/risk-map" },
  { key: "cash", label: "الكاش المتوقع — الشهر القادم", value: formatIQD(ownerKpis.predictedCash), icon: Wallet, tone: "primary", to: "/owner/departments" },
  { key: "eff", label: "كفاءة فريق التدقيق", value: `${ownerKpis.auditorEfficiency}%`, icon: Users, tone: "primary", to: "/owner/ledger" },
];

const toneClass: Record<string, string> = {
  danger: "text-danger border-danger/30 bg-danger/5",
  warning: "text-warning border-warning/30 bg-warning/5",
  success: "text-success border-success/30 bg-success/5",
  primary: "text-primary border-primary/30 bg-primary/5",
};

function OwnerHome() {
  return (
    <div>
      <PageHeader
        title="الصورة الحقيقية"
        subtitle="نظرة تنفيذية مبنية على تحليل مباشر — البيانات لم تغادر شركتك."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <Link
              key={c.key}
              to={c.to}
              className="group p-5 rounded-xl bg-card border border-border hover:border-primary transition relative overflow-hidden"
            >
              <div className={`inline-flex p-2 rounded-lg border ${toneClass[c.tone]}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="text-sm text-muted-foreground mt-4">{c.label}</div>
              <div className="text-2xl font-bold mt-2">{c.value}</div>
              <div className="flex items-center gap-1 text-xs text-primary mt-4 opacity-0 group-hover:opacity-100 transition">
                تفاصيل <ArrowLeft className="w-3 h-3" />
              </div>
            </Link>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">التدفق النقدي — آخر 6 أشهر (مليون د.ع)</h3>
            <span className="text-xs text-muted-foreground">تحديث تلقائي كل 5 دقائق</span>
          </div>
          <div className="h-72">
            <ResponsiveContainer>
              <LineChart data={cashTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.32 0.03 250)" />
                <XAxis dataKey="month" reversed stroke="oklch(0.72 0.02 90)" />
                <YAxis orientation="right" stroke="oklch(0.72 0.02 90)" />
                <Tooltip
                  contentStyle={{ background: "oklch(0.22 0.028 250)", border: "1px solid oklch(0.32 0.03 250)", borderRadius: 8, direction: "rtl" }}
                  labelStyle={{ color: "oklch(0.97 0.01 90)" }}
                />
                <Line type="monotone" dataKey="in" stroke="oklch(0.7 0.16 150)" strokeWidth={2} name="داخل" />
                <Line type="monotone" dataKey="out" stroke="oklch(0.65 0.22 25)" strokeWidth={2} name="خارج" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-card border border-border">
          <h3 className="font-bold mb-4">المسار الموصى به</h3>
          <ol className="space-y-4 text-sm">
            {[
              "مراجعة 7 تنبيهات حرجة في خريطة المخاطر",
              "تأكيد توصية استرداد 12.4 مليون د.ع (فاتورة مكررة)",
              "اطّلاع على تقرير الأداء الأسبوعي للمدققين",
              "تشغيل محاكي القرار للقرار الشهري الكبير",
            ].map((t, i) => (
              <li key={i} className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-primary/15 text-primary text-xs flex items-center justify-center font-bold shrink-0">{i + 1}</span>
                <span className="leading-relaxed">{t}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}