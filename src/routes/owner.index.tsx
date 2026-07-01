import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import {
  TrendingDown,
  ShieldCheck,
  AlertTriangle,
  Wallet,
  Users,
  ArrowLeft,
  Briefcase,
  Sparkles,
  Building2,
  Check,
  ListTodo,
  ScrollText,
  FileBarChart,
  Sliders,
  FileCheck2,
  Bell,
  Server,
  ChevronRight,
  Activity,
  TrendingUp,
} from "lucide-react";
import { getLocale, type Locale } from "@/lib/i18n";
import { getCurrentUser, type AccessibleCompany } from "@/lib/auth";
import { setActiveCompanyId, getActiveCompanyId } from "@/lib/api-client";
import {
  ownerKpis,
  wasteByDepartment,
  riskAlerts,
  pendingDocuments,
  ledgerEntries,
  formatIQD,
} from "@/lib/mock-data";

export const Route = createFileRoute("/owner/")({ component: OwnerHome });

const COPY = {
  ar: {
    title: "لوحة المالك",
    subtitle: "ملخص كامل لكل ما يجري في شركتك — في صفحة واحدة.",
    pickCompany: "اختر الشركة",
    pickHint: "الأرقام في هذه الصفحة تخص الشركة المحددة فقط — لا يتم دمج بيانات الشركات.",
    branches: (n: number) => `${n} فروع`,
    monthly_waste: "إجمالي الهدر الشهري",
    trust_index: "مؤشر الثقة",
    critical_alerts: "تنبيهات حرجة",
    predicted_cash: "الكاش المتوقع",
    auditor_efficiency: "كفاءة فريق التدقيق",
    wasteByDept: "الهدر حسب القسم",
    topRisks: "أبرز المخاطر",
    pendingDocs: "مستندات بانتظار الاعتماد",
    recentActivity: "آخر النشاطات",
    modules: "كل أقسام المنصة",
    nextActions: "الإجراءات الموصى بها",
    narrative: "ملخص استراتيجي",
    narrativeBody:
      "تركّز الجهود هذا الشهر على المشتريات (78.2 مليون د.ع هدر مكتشف) — يوجد 12.4 مليون د.ع قابلة للاسترداد فوراً. مؤشر الثقة 78/100 ضمن المعدل الآمن، لكن 7 تنبيهات حرجة تحتاج قراراً خلال الأسبوع.",
    viewAll: "عرض الكل",
    portfolioLink: "محفظة كاملة",
  },
  ckb: {
    title: "داشبۆردی خاوەن",
    subtitle: "کورتە تەواوی هەرچی لە کۆمپانیاکەتدا ڕوودەدات — لە یەک لاپەڕەدا.",
    pickCompany: "کۆمپانیا هەڵبژێرە",
    pickHint: "ژمارەکانی ئەم لاپەڕەیە تەنها بۆ کۆمپانیای دیاریکراون — داتاکان تێکەڵ ناکرێن.",
    branches: (n: number) => `${n} لق`,
    monthly_waste: "کۆی بەفڕینی مانگانە",
    trust_index: "نیشاندەری متمانە",
    critical_alerts: "ئاگادارکردنەوەی ڕەخنەیی",
    predicted_cash: "پارەی چاوەڕوانکراو",
    auditor_efficiency: "کارایی تیمی پشکنین",
    wasteByDept: "بەفڕین بەپێی بەش",
    topRisks: "گرنگترین مەترسییەکان",
    pendingDocs: "بەڵگەنامەکانی چاوەڕوانی پەسەندکردن",
    recentActivity: "دواین چالاکییەکان",
    modules: "هەموو بەشەکانی پلاتفۆڕم",
    nextActions: "کارە پێشنیارکراوەکان",
    narrative: "کورتی ستراتژی",
    narrativeBody:
      "ئەم مانگە تەرکیز لەسەر کڕینەکانە (٧٨٫٢ ملیۆن د.ع بەفڕینی دۆزراوەتەوە) — ١٢٫٤ ملیۆن د.ع دەکرێت یەکسەر بگەڕێنرێتەوە. نیشاندەری متمانە ٧٨/١٠٠ سەلامەتە، بەڵام ٧ ئاگادارکردنەوەی ڕەخنەیی پێویستیان بە بڕیارە لەم هەفتەیەدا.",
    viewAll: "بینینی هەموو",
    portfolioLink: "پۆرفۆلیۆی تەواو",
  },
} as const;

const toneClass: Record<string, string> = {
  danger: "text-danger border-danger/30 bg-danger/5",
  warning: "text-warning border-warning/30 bg-warning/5",
  success: "text-success border-success/30 bg-success/5",
  primary: "text-primary border-primary/30 bg-primary/5",
};
const toneBar: Record<string, string> = {
  danger: "bg-danger",
  warning: "bg-warning",
  success: "bg-success",
  primary: "bg-primary",
};
const sevTone: Record<string, string> = {
  critical: "danger",
  high: "warning",
  medium: "primary",
};

function OwnerHome() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  const [user] = useState(() => getCurrentUser());
  const [companyId, setCompanyId] = useState<string | null>(null);

  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    const onCompanyChanged = () => {
      const active = getActiveCompanyId();
      const companies = (user?.accessibleCompanies as AccessibleCompany[] | undefined) ?? [];
      const initial =
        active && companies.some((c) => c.company_id === active)
          ? active
          : (companies[0]?.company_id ?? null);
      if (initial && initial !== active) setActiveCompanyId(initial);
      setCompanyId(initial);
    };
    window.addEventListener("storage", onStorage);
    window.addEventListener("auditcore.active_company_changed", onCompanyChanged);
    onCompanyChanged();
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("auditcore.active_company_changed", onCompanyChanged);
    };
  }, [user]);

  const companies = (user?.accessibleCompanies as AccessibleCompany[] | undefined) ?? [];
  const activeCompany = useMemo(
    () => companies.find((c) => c.company_id === companyId) ?? companies[0],
    [companies, companyId],
  );

  const selectCompany = (cid: string) => {
    setActiveCompanyId(cid);
    setCompanyId(cid);
  };

  const t = COPY[locale];
  const maxWaste = Math.max(...wasteByDepartment.map((w) => w.value));

  const kpis = [
    {
      key: "waste",
      label: t.monthly_waste,
      value: formatIQD(ownerKpis.monthlyWaste),
      icon: TrendingDown,
      tone: "danger",
      to: "/owner/waste-map" as const,
    },
    {
      key: "trust",
      label: t.trust_index,
      value: `${ownerKpis.trustIndex} / 100`,
      icon: ShieldCheck,
      tone: ownerKpis.trustIndex >= 80 ? "success" : "warning",
      to: "/owner/trust-index" as const,
    },
    {
      key: "alerts",
      label: t.critical_alerts,
      value: String(ownerKpis.criticalAlerts),
      icon: AlertTriangle,
      tone: "warning",
      to: "/owner/risk-map" as const,
    },
    {
      key: "cash",
      label: t.predicted_cash,
      value: formatIQD(ownerKpis.predictedCash),
      icon: Wallet,
      tone: "primary",
      to: "/owner/what-if" as const,
    },
    {
      key: "eff",
      label: t.auditor_efficiency,
      value: `${ownerKpis.auditorEfficiency}%`,
      icon: Users,
      tone: "success",
      to: "/owner/ledger" as const,
    },
  ];

  const modules = [
    {
      to: "/owner/advisor" as const,
      label: locale === "ar" ? "مستشار المالك الآلي" : "ڕاوێژکاری خۆکار",
      sub: locale === "ar" ? "تدقيق المدقق وتفسير التقارير" : "پشکنینی پشکنەر و وەرگێڕان",
      icon: Sparkles,
    },
    {
      to: "/owner/trust-index" as const,
      label: locale === "ar" ? "مؤشر الثقة" : "نیشاندەری متمانە",
      sub: locale === "ar" ? "صحة بياناتك" : "تەندروستی داتاکانت",
      icon: ShieldCheck,
    },
    {
      to: "/owner/waste-map" as const,
      label: locale === "ar" ? "خريطة الهدر" : "نەخشەی بەفڕین",
      sub: locale === "ar" ? "أين تخسر المال" : "لەکوێ پارە ون دەکەیت",
      icon: TrendingDown,
    },
    {
      to: "/owner/risk-map" as const,
      label: locale === "ar" ? "خريطة المخاطر" : "نەخشەی مەترسی",
      sub: locale === "ar" ? "ما يحتاج قراراً" : "ئەوەی پێویستی بە بڕیارە",
      icon: AlertTriangle,
    },
    {
      to: "/owner/opportunity-map" as const,
      label: locale === "ar" ? "خريطة الفرص" : "نەخشەی دەرفەت",
      sub: locale === "ar" ? "ما يمكن ربحه" : "ئەوەی دەکرێت قازانج بکرێت",
      icon: Sparkles,
    },
    {
      to: "/owner/action-plan" as const,
      label: locale === "ar" ? "خطة العمل" : "پلانی کار",
      sub: locale === "ar" ? "ماذا تفعل الآن" : "ئێستا چی بکەیت",
      icon: ListTodo,
    },
    {
      to: "/owner/what-if" as const,
      label: locale === "ar" ? "محاكي القرار" : "هاوشێوەکاری بڕیار",
      sub: locale === "ar" ? "جرّب قبل التنفيذ" : "تاقیبکەرەوە پێش جێبەجێکردن",
      icon: Sliders,
    },
    {
      to: "/owner/departments" as const,
      label: locale === "ar" ? "الأقسام" : "بەشەکان",
      sub: locale === "ar" ? "أداء كل قسم" : "کارایی هەر بەشێک",
      icon: Building2,
    },
    {
      to: "/owner/portfolio" as const,
      label: locale === "ar" ? "محفظة الشركات" : "پۆرفۆلیۆ",
      sub: locale === "ar" ? "كل شركاتك" : "هەموو کۆمپانیاکانت",
      icon: Briefcase,
    },
    {
      to: "/owner/layer4" as const,
      label: locale === "ar" ? "المستندات الأصلية" : "بەڵگەنامە ئەسڵییەکان",
      sub: locale === "ar" ? "تتبّع المصدر" : "بەدواداچوونی سەرچاوە",
      icon: FileCheck2,
    },
    {
      to: "/owner/ledger" as const,
      label: locale === "ar" ? "السجل" : "تۆمار",
      sub: locale === "ar" ? "غير قابل للتعديل" : "نەگۆڕاو",
      icon: ScrollText,
    },
    {
      to: "/owner/exports" as const,
      label: locale === "ar" ? "التقارير" : "ڕاپۆرتەکان",
      sub: locale === "ar" ? "تصدير وطباعة" : "هەناردە و چاپ",
      icon: FileBarChart,
    },
    {
      to: "/owner/activation" as const,
      label: locale === "ar" ? "التفعيل" : "چالاککردن",
      sub: locale === "ar" ? "حالة الإعداد" : "دۆخی ئامادەکاری",
      icon: Bell,
    },
    {
      to: "/silent-ai" as const,
      label: locale === "ar" ? "الذكاء الصامت" : "زیرەکی بێدەنگ",
      sub: locale === "ar" ? "ضمان عدم الخروج" : "دڵنیایی نەهاتنە دەرەوە",
      icon: ShieldCheck,
    },
    {
      to: "/trust" as const,
      label: locale === "ar" ? "مركز الثقة" : "ناوەندی متمانە",
      sub: locale === "ar" ? "إثبات للعملاء" : "سەلماندن بۆ کڕیار",
      icon: Server,
    },
  ];

  return (
    <div>
      <PageHeader title={t.title} subtitle={t.subtitle} />

      {companies.length > 0 && (
        <div className="mb-6 p-5 rounded-2xl bg-gradient-to-bl from-primary/10 to-card border border-primary/25">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-primary" />
              <span className="text-sm font-bold">{t.pickCompany}</span>
            </div>
            <Link
              to="/owner/portfolio"
              className="text-xs text-primary flex items-center gap-1 hover:underline"
            >
              {t.portfolioLink} <ChevronRight className="w-3 h-3 rtl:rotate-180" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {companies.map((c) => {
              const active = c.company_id === activeCompany?.company_id;
              return (
                <button
                  key={c.company_id}
                  onClick={() => selectCompany(c.company_id)}
                  className={`text-start p-4 rounded-xl border transition-all ${active ? "border-primary bg-primary/10 shadow-[0_8px_24px_-12px_var(--primary)]" : "border-border bg-card hover:border-primary/50"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div
                        className={`p-2 rounded-lg ${active ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}
                      >
                        <Building2 className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-bold text-sm leading-tight">{c.name}</div>
                        <div className="text-[11px] text-muted-foreground mt-0.5">
                          {t.branches(c.branches.length)}
                        </div>
                      </div>
                    </div>
                    {active && <Check className="w-4 h-4 text-primary shrink-0" />}
                  </div>
                </button>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground mt-3 leading-relaxed">{t.pickHint}</p>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 mb-6">
        {kpis.map((c) => {
          const Icon = c.icon;
          return (
            <Link
              key={c.key}
              to={c.to}
              className="group relative overflow-hidden p-4 rounded-2xl border border-border bg-gradient-to-b from-card to-card/60 transition-all hover:-translate-y-0.5 hover:border-primary/50"
            >
              <span className={`absolute inset-x-0 top-0 h-1 ${toneBar[c.tone]} opacity-70`} />
              <div className={`inline-flex p-2 rounded-lg border ${toneClass[c.tone]}`}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="text-xs text-muted-foreground mt-3">{c.label}</div>
              <div className="text-xl font-bold font-display mt-1 tracking-tight">{c.value}</div>
            </Link>
          );
        })}
      </div>

      <div className="p-5 rounded-2xl bg-gradient-to-bl from-primary/10 to-card border border-primary/25 mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <div className="inline-flex p-2 rounded-xl border border-primary/30 bg-primary/15 text-primary shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-primary/80 font-bold mb-1">
              {t.narrative}
            </div>
            <p className="text-sm leading-relaxed">{t.narrativeBody}</p>
          </div>
        </div>
        <Link
          to="/owner/advisor"
          className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/95 font-bold text-xs rounded-xl shrink-0 flex items-center gap-1.5 transition self-end md:self-auto"
        >
          <span>
            {locale === "ar" ? "افتح المستشار الآلي وتدقيق المدقق" : "ڕاوێژکاری خۆکار بکەرەوە"}
          </span>
          <ArrowLeft className="w-3.5 h-3.5 rtl:rotate-180" />
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="lg:col-span-2 p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold font-display flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" /> {t.wasteByDept}
            </h3>
            <Link
              to="/owner/waste-map"
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              {t.viewAll} <ChevronRight className="w-3 h-3 rtl:rotate-180" />
            </Link>
          </div>
          <div className="space-y-3">
            {wasteByDepartment.map((d) => {
              const pct = Math.round((d.value / maxWaste) * 100);
              return (
                <div key={d.name}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span>{d.name}</span>
                    <span className="font-mono text-danger text-xs">{formatIQD(d.value)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-l from-danger to-warning"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold font-display flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" /> {t.topRisks}
            </h3>
            <Link to="/owner/risk-map" className="text-xs text-primary hover:underline">
              {t.viewAll}
            </Link>
          </div>
          <div className="space-y-3">
            {riskAlerts.slice(0, 4).map((r) => {
              const tone = sevTone[r.severity] ?? "primary";
              return (
                <div key={r.id} className={`p-3 rounded-lg border ${toneClass[tone]}`}>
                  <div className="text-sm font-medium leading-snug">{r.title}</div>
                  <div className="flex items-center justify-between mt-2 text-[11px] text-muted-foreground">
                    <span>{r.department}</span>
                    {r.impact > 0 && <span className="font-mono">{formatIQD(r.impact)}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold font-display flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-primary" /> {t.pendingDocs}
            </h3>
            <Link to="/owner/layer4" className="text-xs text-primary hover:underline">
              {t.viewAll}
            </Link>
          </div>
          <div className="space-y-2">
            {pendingDocuments.map((d) => (
              <div
                key={d.id}
                className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/40 transition"
              >
                <div className="p-2 rounded-md bg-primary/10 text-primary">
                  <FileCheck2 className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate" dir="ltr">
                    {d.filename}
                  </div>
                  <div className="text-[11px] text-muted-foreground">{d.category}</div>
                </div>
                <div
                  className={`text-xs font-mono px-2 py-1 rounded ${d.confidence >= 85 ? "bg-success/10 text-success" : d.confidence >= 70 ? "bg-warning/10 text-warning" : "bg-danger/10 text-danger"}`}
                >
                  {d.confidence}%
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold font-display flex items-center gap-2">
              <ScrollText className="w-4 h-4 text-primary" /> {t.recentActivity}
            </h3>
            <Link to="/owner/ledger" className="text-xs text-primary hover:underline">
              {t.viewAll}
            </Link>
          </div>
          <div className="space-y-3">
            {ledgerEntries.map((l) => (
              <div key={l.id} className="flex gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{l.action}</div>
                  <div className="text-xs text-muted-foreground truncate">{l.target}</div>
                  <div className="text-[11px] text-muted-foreground mt-1 flex items-center gap-2">
                    <span>{l.actor}</span>
                    <span>•</span>
                    <span dir="ltr" className="font-mono">
                      {l.at}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="p-5 rounded-2xl bg-card border border-border mb-6">
        <h3 className="font-bold font-display mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary" /> {t.modules}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <Link
                key={m.to}
                to={m.to}
                className="group p-4 rounded-xl border border-border hover:border-primary/60 hover:bg-primary/5 transition flex items-start gap-3"
              >
                <div className="p-2 rounded-lg bg-primary/10 text-primary border border-primary/20 group-hover:bg-primary group-hover:text-primary-foreground transition">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold leading-tight">{m.label}</div>
                  <div className="text-[11px] text-muted-foreground mt-0.5 leading-snug">
                    {m.sub}
                  </div>
                </div>
                <ArrowLeft className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition" />
              </Link>
            );
          })}
        </div>
      </div>

      <div className="p-5 rounded-2xl bg-card border border-border">
        <h3 className="font-bold font-display mb-4 flex items-center gap-2">
          <span className="w-1 h-5 rounded-full bg-primary" /> {t.nextActions}
        </h3>
        <ol className="space-y-3 text-sm">
          {[
            locale === "ar"
              ? "مراجعة 7 تنبيهات حرجة في خريطة المخاطر"
              : "پێداچوونەوەی ٧ ئاگادارکردنەوەی ڕەخنەیی لە نەخشەی مەترسییەکان",
            locale === "ar"
              ? "تأكيد توصية استرداد 12.4 مليون د.ع"
              : "دووبەرەکرنی ڕاسپاردەی گەڕاندنەوەی ١٢٫٤ ملیۆن د.ع",
            locale === "ar"
              ? "اطّلاع على تقرير الأداء الأسبوعي للمدققين"
              : "سەیری ڕاپۆرتی کارایی هەفتانەی پشکنەران",
            locale === "ar"
              ? "تشغيل محاكي القرار للقرار الشهري الكبير"
              : "کارپێکردنی هاوشێوەکاری بڕیار بۆ بڕیاری گەورەی مانگانە",
          ].map((s, i) => (
            <li key={i} className="flex gap-3 items-start group">
              <span className="w-7 h-7 rounded-full bg-primary/15 text-primary text-xs flex items-center justify-center font-bold shrink-0 border border-primary/20 group-hover:bg-primary group-hover:text-primary-foreground transition">
                {i + 1}
              </span>
              <span className="leading-relaxed pt-0.5">{s}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
