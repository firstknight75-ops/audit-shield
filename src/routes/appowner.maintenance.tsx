import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";

const events = [
  {
    at: "2026-06-27 23:14",
    action: "دفع قالب جديد",
    target: "مجموعة النخيل التجارية",
    who: "App Owner",
  },
  {
    at: "2026-06-27 14:02",
    action: "تحديث النسخة → v2.4.1",
    target: "مطاعم بغداد العريقة",
    who: "App Owner",
  },
  {
    at: "2026-06-26 09:30",
    action: "ترقية الباقة → النخبة",
    target: "العقارية المتحدة",
    who: "App Owner",
  },
  {
    at: "2026-06-25 19:00",
    action: "تجديد رخصة سنوية",
    target: "مصنع الفرات للأغذية",
    who: "App Owner",
  },
];

export const Route = createFileRoute("/appowner/maintenance")({
  component: () => (
    <div>
      <PageHeader title="سجل الصيانة" subtitle="كل إجراء عن بُعد مسجّل ومرئي للعميل" />
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary">
            <tr>
              <th className="text-right p-3">الوقت</th>
              <th className="text-right p-3">الإجراء</th>
              <th className="text-right p-3">الهدف</th>
              <th className="text-right p-3">المنفّذ</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e, i) => (
              <tr key={i} className="border-t border-border">
                <td className="p-3 text-muted-foreground" dir="ltr">
                  {e.at}
                </td>
                <td className="p-3">{e.action}</td>
                <td className="p-3 font-medium">{e.target}</td>
                <td className="p-3 text-muted-foreground">{e.who}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  ),
});
