import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ROLE_HOME, ROLE_LABELS, SEEDED_USERS, signIn } from "@/lib/auth";
import { ShieldCheck, Lock } from "lucide-react";
import { getLocale, t } from "@/lib/i18n";

export const Route = createFileRoute("/login")({ head: () => ({ meta: [{ title: "AuditCore Login" }] }), component: Login });

function Login() {
  const navigate = useNavigate();
  const locale = getLocale();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const u = signIn(email, password);
      navigate({ to: ROLE_HOME[u.role], replace: true });
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (u: (typeof SEEDED_USERS)[number]) => {
    setEmail(u.email);
    setPassword(u.password);
  };

  return (
    <div dir="rtl" className="min-h-screen grid lg:grid-cols-2" style={{ fontFamily: 'Noto Sans Arabic, sans-serif' }}>
      <div className="hidden lg:flex flex-col justify-between p-12 bg-sidebar text-sidebar-foreground border-l border-sidebar-border">
        <div className="flex items-center gap-3"><ShieldCheck className="w-8 h-8 text-primary" /><div><div className="text-2xl font-bold">AuditCore</div><div className="text-xs text-muted-foreground">منصة الذكاء التدقيقي السيادي / پلاتفۆرمی ژیری پشکنینی سەربەخۆ</div></div></div>
        <div className="space-y-6"><h1 className="text-4xl font-bold leading-snug">البيانات لا تغادر <span className="text-primary">مكتب الشركة</span></h1><p className="text-muted-foreground leading-loose max-w-md">صلاحيات صارمة، سجل لا يُمحى، وتحليل صامت يكشف الهدر والمخاطر — دون أن يطّلع المدقق على أي استنتاج مالي.</p></div>
        <div className="text-xs text-muted-foreground">© 2026 AuditCore</div>
      </div>
      <div className="flex items-center justify-center p-6 lg:p-12 bg-background">
        <div className="w-full max-w-md space-y-8">
          <div><div className="flex items-center gap-2 mb-2"><Lock className="w-5 h-5 text-primary" /><h2 className="text-2xl font-bold">{t('auth', 'title', locale)}</h2></div><p className="text-sm text-muted-foreground">{t('auth', 'subtitle', locale)}</p></div>
          <form onSubmit={submit} className="space-y-4">
            <div><label className="text-sm font-medium block mb-2">{t('auth', 'email', locale)}</label><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-3 rounded-lg bg-card border border-border focus:border-primary focus:outline-none transition" placeholder="owner@auditcore.local" dir="ltr" /></div>
            <div><label className="text-sm font-medium block mb-2">{t('auth', 'password', locale)}</label><input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-4 py-3 rounded-lg bg-card border border-border focus:border-primary focus:outline-none transition" dir="ltr" /></div>
            {err && <div className="px-4 py-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">{err}</div>}
            <button disabled={loading} className="w-full py-3 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90 transition disabled:opacity-50">{loading ? t('auth', 'loading', locale) : t('auth', 'submit', locale)}</button>
          </form>
          <div className="pt-6 border-t border-border"><div className="text-xs text-muted-foreground mb-3">الحسابات التجريبية</div><div className="grid grid-cols-2 gap-2">{SEEDED_USERS.map((u) => <button key={u.id} type="button" onClick={() => quickFill(u)} className="text-right p-2 rounded-md bg-card border border-border hover:border-primary transition text-xs"><div className="font-bold">{ROLE_LABELS[u.role]}</div><div className="text-muted-foreground truncate" dir="ltr">{u.email}</div></button>)}</div></div>
        </div>
      </div>
    </div>
  );
}
