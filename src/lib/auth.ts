export type Role = "owner" | "gm" | "manager" | "auditor" | "admin" | "appowner";
export type Locale = "ar" | "ckb";

export interface AccessibleBranch {
  branch_id: string;
  name: string;
}

export interface AccessibleCompany {
  company_id: string;
  name: string;
  branches: AccessibleBranch[];
}

export interface SeededUser {
  id: string;
  email: string;
  password: string;
  fullName: string;
  role: Role;
  preferredLanguage: Locale;
  accessibleCompanies?: AccessibleCompany[];
  branch?: string;
  department?: string;
}

export const SEEDED_USERS: SeededUser[] = [
  {
    id: "u-owner",
    email: "owner@auditcore.local",
    password: "Owner123!",
    fullName: "المالك — أبو محمد",
    role: "owner",
    preferredLanguage: "ar",
    accessibleCompanies: [
      {
        company_id: "c1",
        name: "مجموعة الفرات للتجارة",
        branches: [
          { branch_id: "b1", name: "الفرع الرئيسي — بغداد" },
          { branch_id: "b2", name: "فرع البصرة" },
        ],
      },
      {
        company_id: "c2",
        name: "مصنع الفرات للصناعات الغذائية",
        branches: [
          { branch_id: "b3", name: "المعمل — كربلاء" },
          { branch_id: "b4", name: "مستودع النجف" },
        ],
      },
      {
        company_id: "c3",
        name: "مطاعم بغداد العريقة",
        branches: [
          { branch_id: "b5", name: "فرع الكرادة" },
          { branch_id: "b6", name: "فرع المنصور" },
          { branch_id: "b7", name: "فرع زيونة" },
        ],
      },
    ],
  },
  { id: "u-gm", email: "gm@auditcore.local", password: "Gm123!", fullName: "بەڕێوەبەری گشتی — سالم الجبوري", role: "gm", preferredLanguage: "ckb" },
  { id: "u-manager", email: "manager@auditcore.local", password: "Manager123!", fullName: "مدير المشتريات — حسن العاني", role: "manager", preferredLanguage: "ar" },
  { id: "u-auditor", email: "auditor@auditcore.local", password: "Auditor123!", fullName: "ژمێریار — زينب الكاظمي", role: "auditor", preferredLanguage: "ckb" },
  { id: "u-admin", email: "sysadmin@auditcore.local", password: "Sysadmin123!", fullName: "مدير النظام — مصطفى", role: "admin", preferredLanguage: "ar" },
  { id: "u-appowner", email: "appowner@auditcore.local", password: "Appowner123!", fullName: "خاوەنی پلاتفۆڕم — AuditCore", role: "appowner", preferredLanguage: "ckb" },
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

export interface Permission {
  code: string;
  description: string;
  category: "owner" | "gm" | "manager" | "auditor" | "admin" | "app_owner";
}

export const PERMISSIONS: Permission[] = [
  { code: "view_executive", description: "عرض اللوحة التنفيذية", category: "owner" },
  { code: "view_waste_map", description: "عرض خريطة الهدر", category: "owner" },
  { code: "view_risk_map", description: "عرض خريطة المخاطر", category: "owner" },
  { code: "view_ledger", description: "عرض السجل غير القابل للتعديل", category: "owner" },
  { code: "view_departments", description: "عرض كل الأقسام", category: "gm" },
  { code: "view_own_department", description: "عرض القسم الخاص فقط", category: "manager" },
  { code: "manage_tasks", description: "إدارة مهام التصحيح", category: "manager" },
  { code: "certify_document", description: "اعتماد المستندات", category: "auditor" },
  { code: "upload_document", description: "رفع مستندات", category: "auditor" },
  { code: "manage_users", description: "إدارة المستخدمين", category: "admin" },
  { code: "manage_permissions", description: "إدارة الصلاحيات", category: "admin" },
  { code: "manage_branches", description: "إدارة الفروع", category: "admin" },
  { code: "view_activity_log", description: "عرض سجل النشاط", category: "admin" },
  { code: "manage_templates", description: "إدارة قوالب القطاعات", category: "app_owner" },
  { code: "manage_client_companies", description: "إدارة الشركات العميلة", category: "app_owner" },
];

export const ROLE_DEFAULTS: Record<Role, string[]> = {
  owner: ["view_executive", "view_waste_map", "view_risk_map", "view_ledger"],
  gm: ["view_executive", "view_departments"],
  manager: ["view_own_department", "manage_tasks"],
  auditor: ["certify_document", "upload_document"],
  admin: ["manage_users", "manage_permissions", "manage_branches", "view_activity_log"],
  appowner: ["manage_templates", "manage_client_companies"],
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
  const user = SEEDED_USERS.find((u) => u.email.toLowerCase() === email.trim().toLowerCase() && u.password === password);
  if (!user) throw new Error("البريد الإلكتروني أو كلمة المرور غير صحيحة");
  window.localStorage.setItem(KEY, JSON.stringify({ id: user.id, at: Date.now(), preferredLanguage: user.preferredLanguage }));
  return user;
}

export function signOut() {
  window.localStorage.removeItem(KEY);
}

/** Persist preferred language change to backend user record. */
export async function persistLanguageChange(token: string, language: Locale): Promise<void> {
  try {
    await fetch("/api/admin/language", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ preferred_language: language }),
    });
  } catch {
    // Best-effort; the localStorage change already happened client-side.
  }
}
