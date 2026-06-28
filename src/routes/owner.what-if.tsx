import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { formatIQD } from "@/lib/mock-data";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export const Route = createFileRoute("/owner/what-if")({ component: WhatIf });

const baseItem = { desc: "فاتورة مكررة — مورد الرافدين", baseAmount: 12_400_000 };

function WhatIf() {
  const [recovery, setRecovery] = useState(70);
  const [months, setMonths] = useState(6);
  const [cost, setCost] = useState(1_500_000);

  const recovered = (baseItem.baseAmount * recovery) / 100;
  const monthlyImpact = recovered / months - cost / months;
  const netProfit = recovered - cost;

  const data = useMemo(
    () =>
      Array.from({ length: months }, (_, i) => ({
        month: `ش${i + 1}`,
        impact: Math.round(monthlyImpact * (i + 1)),
      })),
    [months, monthlyImpact],
  );

  return (
    <div>
      <PageHeader title="محاكي القرار" subtitle="جرّب السيناريو قبل اتخاذ القرار" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl bg-card border border-border space-y-6">
          <div>
            <div className="text-xs text-muted-foreground mb-1">البند المختار</div>
            <div className="font-bold">{baseItem.desc}</div>
            <div className="text-sm text-danger mt-1">{formatIQD(baseItem.baseAmount)}</div>
          </div>
          <Slider label="نسبة الاسترداد المتوقعة" value={recovery} suffix="%" onChange={setRecovery} min={0} max={100} />
          <Slider label="مدة التنفيذ (شهر)" value={months} suffix="ش" onChange={setMonths} min={1} max={12} />
          <div>
            <label className="text-sm font-medium block mb-2">تكلفة التنفيذ (د.ع)</label>
            <input
              type="number"
              value={cost}
              onChange={(e) => setCost(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-background border border-border"
              dir="ltr"
            />
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <Kpi label="المسترد" value={formatIQD(recovered)} tone="success" />
            <Kpi label="أثر شهري" value={formatIQD(Math.round(monthlyImpact))} tone="primary" />
            <Kpi label="صافي الربح" value={formatIQD(Math.round(netProfit))} tone={netProfit > 0 ? "success" : "danger"} />
          </div>
          <div className="p-6 rounded-xl bg-card border border-border">
            <h3 className="font-bold mb-4">الإسقاط — {months} شهر</h3>
            <div className="h-64">
              <ResponsiveContainer>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.32 0.03 250)" />
                  <XAxis dataKey="month" reversed stroke="oklch(0.72 0.02 90)" />
                  <YAxis orientation="right" stroke="oklch(0.72 0.02 90)" />
                  <Tooltip
                    contentStyle={{ background: "oklch(0.22 0.028 250)", border: "1px solid oklch(0.32 0.03 250)", borderRadius: 8 }}
                    formatter={(v: any) => formatIQD(v)}
                  />
                  <Line type="monotone" dataKey="impact" stroke="oklch(0.78 0.13 82)" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <button className="mt-4 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold">
              تصدير السيناريو كـ PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Slider({ label, value, suffix, onChange, min, max }: any) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2 text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-primary font-bold">{value}{suffix}</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-primary"
      />
    </div>
  );
}

function Kpi({ label, value, tone }: { label: string; value: string; tone: string }) {
  const t: Record<string, string> = {
    success: "text-success border-success/30",
    primary: "text-primary border-primary/30",
    danger: "text-danger border-danger/30",
  };
  return (
    <div className={`p-4 rounded-xl bg-card border ${t[tone]}`}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`text-lg font-bold mt-1 ${t[tone].split(" ")[0]}`}>{value}</div>
    </div>
  );
}