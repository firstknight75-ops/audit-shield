export type Role = "owner" | "gm" | "manager" | "auditor" | "admin" | "appowner";

export interface SeededUser {
  id: string;
  email: string;
  password: string;
  fullName: string;
  role: Role;
  branch?: string;
  department?: string;
}

export const SEEDED_USERS: SeededUser[] = [
  { id: "u-owner", email: "owner@auditcore.local", password: "Owner123!", fullName: "المالك — أبو محمد", role: "owner" },
  { id: "u-gm", email: "gm@auditcore.local", password: "Gm123!", fullName: "المدير العام — سالم الجبوري", role: "gm" },
  { id: "u-manager", email: "manager@auditcore.local", password: "Manager123!", fullName: "مدير المشتريات — حسن العاني", role: "manager", department: "المشتريات", branch: "بغداد - الرئيسي" },
  { id: "u-auditor", email: "auditor@auditcore.local", password: "Auditor123!", fullName: "المدقق — زينب الكاظمي", role: "auditor" },
  { id: "u-admin", email: "sysadmin@auditcore.local", password: "Sysadmin123!", fullName: "مدير النظام — مصطفى", role: "admin" },
  { id: "u-appowner", email: "appowner@auditcore.local", password: "Appowner123!", fullName: "مالك المنصة — AuditCore", role: "appowner" },
];

export const ROLE_LABELS: Record<Role, string> = {
  owner: "المالك",
  gm: "المدير العام",
  manager: "مدير قسم",
  auditor: "مدقق",
  admin: "مدير النظام",
  appowner: "مالك المنصة",
};

export const ROLE_HOME: Record<Role, string> = {
  owner: "/owner",
  gm: "/gm",
  manager: "/manager",
  auditor: "/auditor",
  admin: "/admin",
  appowner: "/appowner",
};

const KEY = "auditcore.session.v1";

export function getCurrentUser(): SeededUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const id = JSON.parse(raw).id as string;
    return SEEDED_USERS.find((u) => u.id === id) ?? null;
  } catch {
    return null;
  }
}

export function signIn(email: string, password: string): SeededUser {
  const user = SEEDED_USERS.find(
    (u) => u.email.toLowerCase() === email.trim().toLowerCase() && u.password === password,
  );
  if (!user) throw new Error("البريد الإلكتروني أو كلمة المرور غير صحيحة");
  window.localStorage.setItem(KEY, JSON.stringify({ id: user.id, at: Date.now() }));
  return user;
}

export function signOut() {
  window.localStorage.removeItem(KEY);
}

// Permission catalogue + role defaults (mock — would live in DB in prod)
export interface Permission {
  code: string;
  description: string;
  category: "dashboard" | "export" | "admin" | "app_owner";
}

export const PERMISSIONS: Permission[] = [
  { code: "view_owner_dashboard", description: "عرض لوحة المالك", category: "dashboard" },
  { code: "view_waste_map", description: "عرض خريطة الهدر", category: "dashboard" },
  { code: "view_risk_map", description: "عرض خريطة المخاطر", category: "dashboard" },
  { code: "view_trust_index", description: "عرض مؤشر الموثوقية", category: "dashboard" },
  { code: "view_manager_dashboard", description: "عرض لوحة المدير", category: "dashboard" },
  { code: "view_auditor_workspace", description: "بيئة عمل المدقق", category: "dashboard" },
  { code: "export_excel", description: "تصدير Excel", category: "export" },
  { code: "export_pdf", description: "تصدير PDF", category: "export" },
  { code: "manage_users", description: "إدارة المستخدمين", category: "admin" },
  { code: "manage_permissions", description: "إدارة الصلاحيات", category: "admin" },
  { code: "manage_branches", description: "إدارة الفروع", category: "admin" },
  { code: "view_activity_log", description: "سجل النشاط", category: "admin" },
  { code: "manage_clients", description: "إدارة الشركات العميلة", category: "app_owner" },
  { code: "manage_tiers", description: "إدارة التراخيص والباقات", category: "app_owner" },
  { code: "manage_templates", description: "محرر القوالب القطاعية", category: "app_owner" },
];

export const ROLE_DEFAULTS: Record<Role, string[]> = {
  owner: ["view_owner_dashboard", "view_waste_map", "view_risk_map", "view_trust_index", "export_excel", "export_pdf", "view_activity_log"],
  gm: ["view_owner_dashboard", "view_waste_map", "view_risk_map", "view_trust_index", "export_pdf"],
  manager: ["view_manager_dashboard", "export_pdf"],
  auditor: ["view_auditor_workspace"],
  admin: ["manage_users", "manage_permissions", "manage_branches", "view_activity_log"],
  appowner: ["manage_clients", "manage_tiers", "manage_templates", "view_activity_log"],
};