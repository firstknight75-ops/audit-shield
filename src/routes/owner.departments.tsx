import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { ownerLayer2, formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/departments")({ component: Departments });

function Departments() {
  return (
    <div>
      <PageHeader title="الطبقة الثانية: تفصيل الأقسام" subtitle="تفكيك الهدر والثقة حسب الأقسام" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ownerLayer2.map((item) => (
          <Link key={item.department} to="/owner/risk-map" className="p-5 rounded-xl bg-card border border-border hover:border-primary transition">
            <div className="text-sm text-muted-foreground">{item.department}</div>
            <div className="text-2xl font-bold mt-1">{item.score}</div>
            <div className="text-danger mt-3 font-bold">{formatIQD(item.amount)}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
