import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ROLE_HOME, ROLE_LABELS, SEEDED_USERS, signIn } from "@/lib/auth";
import { ShieldCheck, Lock } from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "تسجيل الدخول — AuditCore" }] }),
  component: Login,
});

function Login() {
  const navigate = useNavigate();
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
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between p-12 bg-sidebar text-sidebar-foreground border-l border-sidebar-border">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-primary" />
          <div>
            <div className="text-2xl font-bold">AuditCore</div>
            <div className="text-xs text-muted-foreground">منصة الذكاء التدقيقي السيادي</div>
          </div>
        </div>
        <div className="space-y-6">
          <h1 className="text-4xl font-bold leading-snug">
            البيانات لا تغادر <span className="text-primary">مكتب الشركة</span>
          </h1>
          <p className="text-muted-foreground leading-loose max-w-md">
            صلاحيات صارمة، سجل لا يُمحى، وتحليل صامت يكشف الهدر والمخاطر — دون أن يطّلع المدقق على أي استنتاج مالي.
          </p>
          <div className="grid grid-cols-3 gap-3 text-center pt-6">
            {[
              { n: "0", t: "تسريب بيانات" },
              { n: "100%", t: "سيادة كاملة" },
              { n: "AES-256", t: "تشفير" },
            ].map((s) => (
              <div key={s.t} className="p-4 rounded-lg bg-sidebar-accent border border-sidebar-border">
                <div className="text-2xl font-bold text-primary">{s.n}</div>
                <div className="text-xs text-muted-foreground mt-1">{s.t}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="text-xs text-muted-foreground">© 2026 AuditCore — جميع الحقوق محفوظة</div>
      </div>

      <div className="flex items-center justify-center p-6 lg:p-12 bg-background">
        <div className="w-full max-w-md space-y-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Lock className="w-5 h-5 text-primary" />
              <h2 className="text-2xl font-bold">تسجيل الدخول</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              ادخل بياناتك للوصول إلى لوحة التحكم
            </p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-2">البريد الإلكتروني</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-card border border-border focus:border-primary focus:outline-none transition"
                placeholder="owner@auditcore.local"
                dir="ltr"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">كلمة المرور</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-card border border-border focus:border-primary focus:outline-none transition"
                dir="ltr"
              />
            </div>
            {err && (
              <div className="px-4 py-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">
                {err}
              </div>
            )}
            <button
              disabled={loading}
              className="w-full py-3 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90 transition disabled:opacity-50"
            >
              {loading ? "جاري التحقق..." : "دخول"}
            </button>
          </form>

          <div className="pt-6 border-t border-border">
            <div className="text-xs text-muted-foreground mb-3">الحسابات التجريبية — اضغط للملء التلقائي</div>
            <div className="grid grid-cols-2 gap-2">
              {SEEDED_USERS.map((u) => (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => quickFill(u)}
                  className="text-right p-2 rounded-md bg-card border border-border hover:border-primary transition text-xs"
                >
                  <div className="font-bold">{ROLE_LABELS[u.role]}</div>
                  <div className="text-muted-foreground truncate" dir="ltr">{u.email}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}