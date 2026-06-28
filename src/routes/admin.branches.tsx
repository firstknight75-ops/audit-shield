import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { Building2, Plus } from "lucide-react";

const branches = [
  { id: "b1", name: "بغداد - الرئيسي", location: "الكرادة", users: 18 },
  { id: "b2", name: "البصرة", location: "العشار", users: 9 },
  { id: "b3", name: "أربيل", location: "عنكاوا", users: 6 },
  { id: "b4", name: "الموصل", location: "الدواسة", users: 4 },
];

export const Route = createFileRoute("/admin/branches")({
  component: () => (
    <div>
      <PageHeader
        title="الفروع"
        action={
          <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold">
            <Plus className="w-4 h-4" /> إضافة فرع
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {branches.map((b) => (
          <div key={b.id} className="p-5 rounded-xl bg-card border border-border">
            <Building2 className="w-6 h-6 text-primary mb-3" />
            <div className="font-bold">{b.name}</div>
            <div className="text-xs text-muted-foreground mt-1">{b.location}</div>
            <div className="text-sm mt-3 pt-3 border-t border-border">{b.users} مستخدم</div>
          </div>
        ))}
      </div>
    </div>
  ),
});