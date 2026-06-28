export type Role = "owner" | "gm" | "manager" | "auditor" | "admin" | "appowner";
export type Locale = "ar" | "ckb";

export interface SeededUser {
  id: string;
  email: string;
  password: string;
  fullName: string;
  role: Role;
  preferredLanguage: Locale;
  branch?: string;
  department?: string;
}

export const SEEDED_USERS: SeededUser[] = [
  { id: "u-owner", email: "owner@auditcore.local", password: "Owner123!", fullName: "المالك — أبو محمد", role: "owner", preferredLanguage: "ar" },
  { id: "u-gm", email: "gm@auditcore.local", password: "Gm123!", fullName: "بەڕێوەبەری گشتی — سالم الجبوري", role: "gm", preferredLanguage: "ckb" },
  { id: "u-manager", email: "manager@auditcore.local", password: "Manager123!", fullName: "مدير المشتريات — حسن العاني", role: "manager", preferredLanguage: "ar", department: "المشتريات", branch: "بغداد - الرئيسي" },
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
