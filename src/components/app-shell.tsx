import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { ReactNode, useEffect, useState } from "react";
import { ShieldCheck, LayoutDashboard, FileCheck2, ListTodo, AlertTriangle, Users, KeyRound, Building2, ScrollText, Boxes, Settings2, FileBarChart, LogOut, Bell, Briefcase, Sparkles, Sliders } from "lucide-react";
import { Role, ROLE_LABELS, getCurrentUser, signOut } from "@/lib/auth";
import { getLocale, setLocale, t } from "@/lib/i18n";

type NavItem = { to: string; label: string; icon: any };

const NAV: Record<Role, NavItem[]> = {
  owner: [
    { to: "/owner", label: "executive_view", icon: LayoutDashboard },
    { to: "/owner/departments", label: "departments", icon: Building2 },
    { to: "/owner/waste-map", label: "waste_map", icon: AlertTriangle },
    { to: "/owner/risk-map", label: "risk_map", icon: AlertTriangle },
    { to: "/owner/what-if", label: "decision_simulator", icon: Sliders },
    { to: "/owner/ledger", label: "السجل غير القابل للتعديل", icon: ScrollText },
    { to: "/owner/exports", label: "التقارير والتصدير", icon: FileBarChart },
  ],
  gm: [
    { to: "/gm", label: "executive_view", icon: LayoutDashboard },
    { to: "/gm/departments", label: "departments", icon: Building2 },
  ],
  manager: [
    { to: "/manager", label: "لوحة القسم", icon: LayoutDashboard },
    { to: "/manager/tasks", label: "مهام التصحيح", icon: ListTodo },
  ],
  auditor: [
    { to: "/auditor", label: "بيئة الاعتماد", icon: FileCheck2 },
    { to: "/auditor/tasks", label: "مهامي اليومية", icon: ListTodo },
    { to: "/auditor/upload", label: "رفع مستند", icon: Boxes },
  ],
  admin: [
    { to: "/admin", label: "إدارة المستخدمين", icon: Users },
    { to: "/admin/permissions", label: "مصفوفة الصلاحيات", icon: KeyRound },
    { to: "/admin/branches", label: "الفروع", icon: Building2 },
    { to: "/admin/activity", label: "سجل النشاط", icon: ScrollText },
  ],
  appowner: [
    { to: "/appowner", label: "الشركات العميلة", icon: Briefcase },
    { to: "/appowner/templates", label: "محرر القوالب", icon: Sparkles },
    { to: "/appowner/maintenance", label: "سجل الصيانة", icon: Settings2 },
  ],
};

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(() => getCurrentUser());
  const [locale, setLocalState] = useState(getLocale());
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    const u = getCurrentUser();
    if (!u) navigate({ to: "/login", replace: true });
    else setUser(u);
  }, [navigate]);

  if (!user) return null;
  const items = NAV[user.role];

  return (
    <div dir="rtl" className="min-h-screen flex w-full bg-background text-foreground">
      <aside className="w-64 bg-sidebar border-l border-sidebar-border flex flex-col">
        <div className="p-5 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-primary" />
            <div>
              <div className="font-bold leading-tight">AuditCore</div>
              <div className="text-[10px] text-muted-foreground">{ROLE_LABELS[user.role]}</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {items.map((it) => {
            const active = pathname === it.to || (it.to !== "/" && pathname.startsWith(it.to + "/"));
            const Icon = it.icon;
            return (
              <Link key={it.to} to={it.to} className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition ${active ? "bg-primary/15 text-primary border border-primary/30" : "text-sidebar-foreground hover:bg-sidebar-accent"}`}>
                <Icon className="w-4 h-4 shrink-0" />
                <span>{it.label.includes('_') ? t('dashboard', it.label, locale) : it.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-sidebar-border">
          <div className="px-3 py-2 mb-2">
            <div className="text-xs font-bold truncate">{user.fullName}</div>
            <div className="text-[10px] text-muted-foreground truncate" dir="ltr">{user.email}</div>
          </div>
          <div className="mb-2 flex items-center justify-between text-xs">
            <span>{t('auth', 'language', locale)}</span>
            <button onClick={() => { const next = locale === 'ar' ? 'ckb' : 'ar'; setLocale(next); setLocalState(next); }} className="px-2 py-1 rounded border border-border">{locale === 'ar' ? 'زمان' : 'لغة'}</button>
          </div>
          <button onClick={() => { signOut(); navigate({ to: "/login", replace: true }); }} className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-sidebar-accent text-muted-foreground">
            <LogOut className="w-4 h-4" />
            {t('auth', 'logout', locale)}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-card/50">
          <div className="text-sm text-muted-foreground">{new Date().toLocaleDateString(locale === 'ar' ? 'ar-IQ' : 'ku', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
          <div className="flex items-center gap-3"><button className="relative w-9 h-9 rounded-md bg-card border border-border flex items-center justify-center hover:border-primary transition"><Bell className="w-4 h-4" /><span className="absolute -top-1 -left-1 w-4 h-4 rounded-full bg-danger text-[10px] text-white flex items-center justify-center">3</span></button></div>
        </header>
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return <div className="flex items-start justify-between mb-6 pb-4 border-b border-border"><div><h1 className="text-2xl font-bold">{title}</h1>{subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}</div>{action}</div>;
}
