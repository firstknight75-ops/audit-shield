import { createFileRoute } from "@tanstack/react-router";
import { wasteByDepartment, wasteByCategory, formatIQD } from "@/lib/mock-data";
import { PageHeader } from "@/components/app-shell";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, PieChart, Pie, Cell, CartesianGrid } from "recharts";

export const Route = createFileRoute("/owner/departments")({ component: Departments });

const COLORS = ["oklch(0.78 0.13 82)", "oklch(0.7 0.16 150)", "oklch(0.65 0.22 25)", "oklch(0.6 0.15 240)"];

function Departments() {
  return (
    <div>
      <PageHeader title="الطبقة الثانية — أداء الأقسام" subtitle="الهدر موزعاً على الأقسام والفئات" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="p-6 rounded-xl bg-card border border-border">
          <h3 className="font-bold mb-4">الهدر حسب القسم</h3>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={wasteByDepartment}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.32 0.03 250)" />
                <XAxis dataKey="name" reversed stroke="oklch(0.72 0.02 90)" />
                <YAxis orientation="right" stroke="oklch(0.72 0.02 90)" />
                <Tooltip
                  contentStyle={{ background: "oklch(0.22 0.028 250)", border: "1px solid oklch(0.32 0.03 250)", borderRadius: 8 }}
                  formatter={(v: any) => formatIQD(v)}
                />
                <Bar dataKey="value" fill="oklch(0.78 0.13 82)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="p-6 rounded-xl bg-card border border-border">
          <h3 className="font-bold mb-4">الهدر حسب الفئة</h3>
          <div className="h-72">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={wasteByCategory} dataKey="value" nameKey="name" outerRadius={100} label>
                  {wasteByCategory.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "oklch(0.22 0.028 250)", border: "1px solid oklch(0.32 0.03 250)", borderRadius: 8 }}
                  formatter={(v: any) => formatIQD(v)}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary text-secondary-foreground">
            <tr>
              <th className="text-right p-3">القسم</th>
              <th className="text-right p-3">الهدر</th>
              <th className="text-right p-3">النسبة من الإجمالي</th>
              <th className="text-right p-3"></th>
            </tr>
          </thead>
          <tbody>
            {wasteByDepartment.map((d) => {
              const total = wasteByDepartment.reduce((a, b) => a + b.value, 0);
              const pct = ((d.value / total) * 100).toFixed(1);
              return (
                <tr key={d.name} className="border-t border-border hover:bg-secondary/50">
                  <td className="p-3 font-medium">{d.name}</td>
                  <td className="p-3">{formatIQD(d.value)}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 max-w-[120px] h-2 rounded-full bg-secondary overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-xs text-muted-foreground">{pct}%</span>
                    </div>
                  </td>
                  <td className="p-3 text-left">
                    <button className="text-xs text-primary hover:underline">عرض التحليل ←</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}