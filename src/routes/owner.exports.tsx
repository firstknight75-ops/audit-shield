import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { FileSpreadsheet, FileText, Image } from "lucide-react";

export const Route = createFileRoute("/owner/exports")({ component: Exports });

const reports = [
  { name: "خريطة الهدر — الشهر الحالي", formats: ["xlsx", "pdf", "png"] },
  { name: "خريطة المخاطر التفصيلية", formats: ["pdf", "png"] },
  { name: "تقرير الموثوقية الأسبوعي", formats: ["pdf"] },
  { name: "الصورة الحقيقية — تقرير تنفيذي", formats: ["pdf"] },
];

const icons: Record<string, any> = { xlsx: FileSpreadsheet, pdf: FileText, png: Image };

function Exports() {
  return (
    <div>
      <PageHeader
        title="التقارير والتصدير"
        subtitle="كل تقرير موقّع بشهادة عدم تلاعب مرتبطة بالسجل"
      />
      <div className="space-y-3">
        {reports.map((r) => (
          <div
            key={r.name}
            className="p-5 rounded-xl bg-card border border-border flex items-center justify-between"
          >
            <div>
              <div className="font-medium">{r.name}</div>
              <div className="text-xs text-muted-foreground mt-1">
                صالح للمشاركة عبر رابط موقّع لمدة 15 دقيقة
              </div>
            </div>
            <div className="flex gap-2">
              {r.formats.map((f) => {
                const Icon = icons[f];
                return (
                  <button
                    key={f}
                    className="flex items-center gap-2 px-3 py-2 rounded-md bg-secondary text-sm hover:bg-primary hover:text-primary-foreground transition"
                  >
                    <Icon className="w-4 h-4" /> {f.toUpperCase()}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
