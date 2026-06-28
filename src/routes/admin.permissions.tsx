import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { PERMISSIONS, ROLE_DEFAULTS, ROLE_LABELS, SEEDED_USERS } from "@/lib/auth";
import { Check, Minus } from "lucide-react";

export const Route = createFileRoute("/admin/permissions")({ component: PermissionsMatrix });

type Override = { user: string; perm: string; effect: "grant" | "revoke"; reason: string; expires?: string };

function PermissionsMatrix() {
  const visible = SEEDED_USERS.filter((u) => u.role !== "appowner");
  const [overrides, setOverrides] = useState<Override[]>([
    { user: "u-manager", perm: "view_waste_map", effect: "grant", reason: "اجتماع المالك الأسبوعي", expires: "2026-07-05" },
  ]);
  const [dialog, setDialog] = useState<{ user: string; perm: string } | null>(null);
  const [reason, setReason] = useState("");
  const [expires, setExpires] = useState("");

  const has = (uid: string, role: string, code: string): "default" | "granted" | "revoked" => {
    const ov = overrides.find((o) => o.user === uid && o.perm === code);
    if (ov) return ov.effect === "grant" ? "granted" : "revoked";
    return ROLE_DEFAULTS[role as keyof typeof ROLE_DEFAULTS]?.includes(code) ? "default" : "default";
  };

  const isOn = (uid: string, role: string, code: string) => {
    const state = has(uid, role, code);
    if (state === "granted") return true;
    if (state === "revoked") return false;
    return ROLE_DEFAULTS[role as keyof typeof ROLE_DEFAULTS]?.includes(code);
  };

  const toggle = (uid: string, role: string, code: string) => {
    // Hard rule: block app_owner permissions
    const perm = PERMISSIONS.find((p) => p.code === code)!;
    if (perm.category === "app_owner") {
      alert("لا يمكن لمدير النظام منح صلاحيات مالك المنصة.");
      return;
    }
    setDialog({ user: uid, perm: code });
    setReason("");
    setExpires("");
  };

  const confirm = () => {
    if (!dialog || !reason) return;
    const isDefault = (() => {
      const u = visible.find((x) => x.id === dialog.user)!;
      return ROLE_DEFAULTS[u.role].includes(dialog.perm);
    })();
    setOverrides((prev) => [
      ...prev.filter((o) => !(o.user === dialog.user && o.perm === dialog.perm)),
      { user: dialog.user, perm: dialog.perm, effect: isDefault ? "revoke" : "grant", reason, expires: expires || undefined },
    ]);
    setDialog(null);
  };

  return (
    <div>
      <PageHeader
        title="مصفوفة الصلاحيات"
        subtitle="رمادي = افتراضي حسب الدور · أصفر = تعديل صريح · يتطلب سبباً ومدة اختيارية"
      />
      <div className="rounded-xl bg-card border border-border overflow-x-auto">
        <table className="w-full text-sm min-w-[700px]">
          <thead className="bg-secondary sticky top-0">
            <tr>
              <th className="text-right p-3 sticky right-0 bg-secondary">الصلاحية</th>
              {visible.map((u) => (
                <th key={u.id} className="p-3 text-center text-xs">
                  <div className="font-bold">{ROLE_LABELS[u.role]}</div>
                  <div className="text-[10px] text-muted-foreground font-normal">{u.fullName.split("—")[0]}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERMISSIONS.map((p) => (
              <tr key={p.code} className="border-t border-border">
                <td className="p-3 sticky right-0 bg-card">
                  <div className="font-medium">{p.description}</div>
                  <div className="text-[10px] text-muted-foreground font-mono" dir="ltr">{p.code}</div>
                </td>
                {visible.map((u) => {
                  const state = has(u.id, u.role, p.code);
                  const on = isOn(u.id, u.role, p.code);
                  const explicit = state !== "default";
                  return (
                    <td key={u.id} className="p-3 text-center">
                      <button
                        onClick={() => toggle(u.id, u.role, p.code)}
                        className={`w-7 h-7 rounded-md inline-flex items-center justify-center border transition ${
                          explicit
                            ? "bg-warning/15 border-warning text-warning"
                            : on
                            ? "bg-success/10 border-success/40 text-success"
                            : "bg-secondary border-border text-muted-foreground"
                        }`}
                      >
                        {on ? <Check className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {dialog && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-card border border-border rounded-xl p-6">
            <h3 className="font-bold text-lg mb-1">تعديل صلاحية</h3>
            <p className="text-xs text-muted-foreground mb-4">سيتم تسجيل هذا التعديل في السجل غير القابل للتعديل.</p>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium block mb-1">السبب (إلزامي)</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-background border border-border"
                  rows={3}
                />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">تاريخ الانتهاء (اختياري)</label>
                <input
                  type="date"
                  value={expires}
                  onChange={(e) => setExpires(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-background border border-border"
                  dir="ltr"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6 justify-end">
              <button onClick={() => setDialog(null)} className="px-4 py-2 rounded-md bg-secondary text-sm">إلغاء</button>
              <button onClick={confirm} disabled={!reason} className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold disabled:opacity-50">تطبيق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}