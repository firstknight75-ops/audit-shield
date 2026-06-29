import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { ReactNode, useEffect, useState } from "react";
import { ShieldCheck, LayoutDashboard, FileCheck2, ListTodo, AlertTriangle, Users, KeyRound, Building2, ScrollText, Boxes, Settings2, FileBarChart, LogOut, Bell, Briefcase, Sparkles, Sliders, Server } from "lucide-react";
import { Role, ROLE_LABELS, getCurrentUser, signOut, persistLanguageChange } from "@/lib/auth";
import { getLocale, setLocale, t, type Namespace } from "@/lib/i18n";
import { CompanySwitcher } from "@/components/company-switcher";

type NavItem = { to: string; label: string; ns: Namespace; icon: any };

const NAV: Record<Role, NavItem[]> = {
  owner: [
    { to: "/owner", label: "executive_view", ns: "dashboard", icon: LayoutDashboard },
    { to: "/owner/trust-index", label: "trust_index", ns: "dashboard", icon: ShieldCheck },
    { to: "/owner/waste-map", label: "waste_map", ns: "dashboard", icon: AlertTriangle },
    { to: "/owner/opportunity-map", label: "opportunity_map", ns: "dashboard", icon: Sparkles },
    { to: "/owner/risk-map", label: "risk_map", ns: "dashboard", icon: AlertTriangle },
    { to: "/owner/action-plan", label: "action_plan", ns: "dashboard", icon: ListTodo },
    { to: "/owner/layer4", label: "layer4_viewer", ns: "dashboard", icon: FileCheck2 },
    { to: "/owner/portfolio", label: "portfolio", ns: "dashboard", icon: Briefcase },
    { to: "/owner/activation", label: "activation", ns: "dashboard", icon: Bell },
    { to: "/owner/departments", label: "departments", ns: "dashboard", icon: Building2 },
    { to: "/owner/what-if", label: "decision_simulator", ns: "dashboard", icon: Sliders },
    { to: "/owner/ledger", label: "ledger", ns: "dashboard", icon: ScrollText },
    { to: "/owner/exports", label: "exports", ns: "dashboard", icon: FileBarChart },
    { to: "/silent-ai", label: "silent_ai", ns: "dashboard", icon: ShieldCheck },
    { to: "/trust", label: "trust_center", ns: "dashboard", icon: Server },
  ],
  gm: [
    { to: "/gm", label: "executive_view", ns: "dashboard", icon: LayoutDashboard },
    { to: "/gm/departments", label: "departments", ns: "dashboard", icon: Building2 },
  ],
  manager: [
    { to: "/manager", label: "department_dashboard", ns: "dashboard", icon: LayoutDashboard },
    { to: "/manager/tasks", label: "correction_tasks", ns: "dashboard", icon: ListTodo },
  ],
  auditor: [
    { to: "/auditor", label: "certification_env", ns: "certification", icon: FileCheck2 },
    { to: "/auditor/tasks", label: "my_daily_tasks", ns: "dashboard", icon: ListTodo },
    { to: "/auditor/upload", label: "upload_document", ns: "dashboard", icon: Boxes },
  ],
  admin: [
    { to: "/admin", label: "users", ns: "admin", icon: Users },
    { to: "/admin/permissions", label: "permissions", ns: "admin", icon: KeyRound },
    { to: "/admin/branches", label: "branches", ns: "admin", icon: Building2 },
    { to: "/admin/activity", label: "activity", ns: "admin", icon: ScrollText },
  ],
  appowner: [
    { to: "/appowner", label: "client_companies", ns: "admin", icon: Briefcase },
    { to: "/appowner/isolation-proof", label: "isolation_proof", ns: "dashboard", icon: ShieldCheck },
    { to: "/appowner/templates", label: "template_editor", ns: "admin", icon: Sparkles },
    { to: "/appowner/maintenance", label: "maintenance_log", ns: "admin", icon: Settings2 },
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

  const handleLanguageToggle = async () => {
    const next = locale === "ar" ? "ckb" : "ar";
    setLocale(next);
    setLocalState(next);
    // Best-effort persist to backend
    const sessionRaw = typeof window !== "undefined" ? window.localStorage.getItem("auditcore.session.v1") : null;
    if (sessionRaw) {
      try {
        const { id } = JSON.parse(sessionRaw);
        // For the demo seeded-user flow, we don't have a real JWT yet,
        // so persistLanguageChange is called with a placeholder.
        // When real auth is wired, this will use the actual access token.
        await persistLanguageChange(id, next);
      } catch {
        // ignore
      }
    }
  };

  return (
    <div dir="rtl" className="min-h-screen flex w-full bg-background text-foreground" style={{ fontFamily: "'Noto Sans Arabic', 'Noto Sans Arabic UI', sans-serif" }}>
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
                <span>{t(it.ns, it.label, locale)}</span>
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
            <span>لغة / زمان</span>
            <button onClick={handleLanguageToggle} className="px-2 py-1 rounded border border-border hover:bg-sidebar-accent transition">
              {locale === "ar" ? "زمان" : "لغة"}
            </button>
          </div>
          <button onClick={() => { signOut(); navigate({ to: "/login", replace: true }); }} className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-sidebar-accent text-muted-foreground">
            <LogOut className="w-4 h-4" />
            {t("auth", "logout", locale)}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-card/50 gap-4">
          <div className="flex items-center gap-4">
            <CompanySwitcher />
          </div>
          <div className="text-sm text-muted-foreground hidden md:block">{new Date().toLocaleDateString(locale === "ar" ? "ar-IQ" : "ku", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</div>
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
