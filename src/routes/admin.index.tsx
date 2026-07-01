import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app-shell";
import { SEEDED_USERS, ROLE_LABELS } from "@/lib/auth";
import { UserPlus, KeyRound, Power } from "lucide-react";

export const Route = createFileRoute("/admin/")({ component: AdminUsers });

function AdminUsers() {
  const visible = SEEDED_USERS.filter((u) => u.role !== "appowner");
  return (
    <div>
      <PageHeader
        title="المستخدمون"
        subtitle="إدارة حسابات الشركة — لا يمكن منح صلاحيات مالك المنصة من هنا"
        action={
          <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold">
            <UserPlus className="w-4 h-4" /> إضافة مستخدم
          </button>
        }
      />
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary">
            <tr>
              <th className="text-right p-3">الاسم</th>
              <th className="text-right p-3">البريد</th>
              <th className="text-right p-3">الدور</th>
              <th className="text-right p-3">القسم/الفرع</th>
              <th className="text-right p-3">الحالة</th>
              <th className="text-right p-3"></th>
            </tr>
          </thead>
          <tbody>
            {visible.map((u) => (
              <tr key={u.id} className="border-t border-border hover:bg-secondary/40">
                <td className="p-3 font-medium">{u.fullName}</td>
                <td className="p-3 text-muted-foreground" dir="ltr">
                  {u.email}
                </td>
                <td className="p-3">
                  <span className="text-xs px-2 py-1 rounded-md bg-primary/10 text-primary border border-primary/30">
                    {ROLE_LABELS[u.role]}
                  </span>
                </td>
                <td className="p-3 text-muted-foreground">{u.branch || u.department || "—"}</td>
                <td className="p-3">
                  <span className="text-xs text-success">نشط</span>
                </td>
                <td className="p-3 text-left flex gap-1 justify-end">
                  <button className="p-2 rounded-md hover:bg-secondary">
                    <KeyRound className="w-4 h-4" />
                  </button>
                  <button className="p-2 rounded-md hover:bg-danger/10 text-danger">
                    <Power className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
