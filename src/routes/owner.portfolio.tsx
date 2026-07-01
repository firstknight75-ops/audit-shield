import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import {
  Briefcase,
  ShieldCheck,
  AlertTriangle,
  TrendingDown,
  Sparkles,
  ArrowLeft,
} from "lucide-react";
import { getLocale, type Locale } from "@/lib/i18n";
import { formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/portfolio")({ component: Portfolio });

// Per Phase 3 spec: side-by-side display must be EXPLICITLY labeled
// "عرض جنباً إلى جنب — بدون دمج الأرقام". This is a UI rule, not just
// a backend rule.

const COPY = {
  ar: {
    title: "محفظة الشركات",
    subtitle: "كل شركة تُعرض على حدة — الأرقام لا تُمزج بصمت.",
    sideBySide: "عرض جنباً إلى جنب — بدون دمج الأرقام",
    noBlend:
      "هذه أرقام منفصلة لكل شركة. لا يتم دمجها تلقائياً — هذا ليس مجرد قاعدة في الخادم، بل قاعدة في الواجهة أيضاً.",
    branchCount: (n: number) => `${n} فروع`,
    goTo: "الانتقال إلى اللوحة التنفيذية",
    empty: "لا توجد شركات في محفظتك.",
    trustLabel: "مؤشر الموثوقية",
    wasteLabel: "الهدر",
    risksLabel: "المخاطر",
    opportunityLabel: "الفرص",
  },
  ckb: {
    title: "پۆرفۆلیۆی کۆمپانیاکان",
    subtitle: "هەر کۆمپانیایەک بە تەنها پیشاندراوە — ژمارەکان بە بێدەنگی تێکەڵ ناکرێن.",
    sideBySide: "پیشاندانی لاتەنیشت — بەبێ تێکەڵکردنی ژمارەکان",
    noBlend:
      "ئەمانە ژمارەی جیاکراوەن بۆ هەر کۆمپانیایەک. بە خۆکار تێکەڵ ناکرێن — ئەمە تەنها یاسایەکی ڕاژەکار نییە، بەڵکو یاسایەکی ڕووکارە.",
    branchCount: (n: number) => `${n} لق`,
    goTo: "بەڕێوەچوون بۆ داشبۆردی جێبەجێکار",
    empty: "هیچ کۆمپانیایەک لە پۆرفۆلیۆکەتدا نییە.",
    trustLabel: "نیشاندەری متمانە",
    wasteLabel: "بەفڕین",
    risksLabel: "مەترسییەکان",
    opportunityLabel: "دەرفەتەکان",
  },
} as const;

const companies = [
  {
    company_id: "c1",
    company_name: "شركة الفرات للتجارة",
    trust_index_score: 80,
    monthly_waste_iqd: 1_500_000,
    critical_alerts: 2,
    opportunity_iqd: 4_500_000,
    risk_alerts: 5,
    documents_total: 220,
    branch_count: 2,
  },
  {
    company_id: "c2",
    company_name: "مصنع الفرات للصناعات",
    trust_index_score: 65,
    monthly_waste_iqd: 3_200_000,
    critical_alerts: 4,
    opportunity_iqd: 1_800_000,
    risk_alerts: 9,
    documents_total: 180,
    branch_count: 2,
  },
];

const totals = {
  monthly_waste_iqd: companies.reduce((s, c) => s + c.monthly_waste_iqd, 0),
  opportunity_iqd: companies.reduce((s, c) => s + c.opportunity_iqd, 0),
  risk_alerts: companies.reduce((s, c) => s + c.risk_alerts, 0),
  documents_total: companies.reduce((s, c) => s + c.documents_total, 0),
};

function Portfolio() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const t = COPY[locale];
  const totalsLabel =
    locale === "ar" ? `مجموع ${companies.length} شركات:` : `کۆی ${companies.length} کۆمپانیا:`;

  return (
    <div>
      <PageHeader title={t.title} subtitle={t.subtitle} />

      {/* Phase 3 — explicit side-by-side label, prominent */}
      <div className="p-5 rounded-2xl bg-warning/10 border-2 border-warning/40 mb-4 flex items-start gap-3">
        <AlertTriangle className="w-6 h-6 text-warning shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="font-bold text-warning text-base">{t.sideBySide}</div>
          <div className="text-sm text-muted-foreground mt-2 leading-relaxed">{t.noBlend}</div>
        </div>
      </div>

      {companies.length === 0 && (
        <div className="p-8 rounded-xl bg-card border border-border text-center text-muted-foreground">
          {t.empty}
        </div>
      )}

      <div className="space-y-4 mb-8">
        {companies.map((c) => (
          <div
            key={c.company_id}
            className="p-6 rounded-2xl bg-card border border-border hover:border-primary/50 transition group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-primary/10 text-primary border border-primary/30">
                  <Briefcase className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">{c.company_name}</h3>
                  <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                    <span className="font-mono">{c.company_id}</span>
                    <span>•</span>
                    <span>{t.branchCount(c.branch_count)}</span>
                  </div>
                </div>
              </div>
              <div className="text-end">
                <div className="text-xs text-muted-foreground uppercase tracking-wide">
                  {t.trustLabel}
                </div>
                <div
                  className={`text-3xl font-bold font-display mt-1 ${c.trust_index_score >= 80 ? "text-success" : c.trust_index_score >= 60 ? "text-warning" : "text-danger"}`}
                >
                  {c.trust_index_score}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-border">
              <Stat
                icon={TrendingDown}
                label={t.wasteLabel}
                value={formatIQD(c.monthly_waste_iqd)}
                tone="danger"
              />
              <Stat
                icon={AlertTriangle}
                label={t.risksLabel}
                value={String(c.risk_alerts)}
                sub={`${c.critical_alerts} ${locale === "ar" ? "حرجة" : "ڕەخنەیی"}`}
                tone="warning"
              />
              <Stat
                icon={Sparkles}
                label={t.opportunityLabel}
                value={formatIQD(c.opportunity_iqd)}
                tone="success"
              />
              <Stat
                icon={ShieldCheck}
                label={locale === "ar" ? "المستندات" : "بەڵگەنامەکان"}
                value={String(c.documents_total)}
                tone="primary"
              />
            </div>

            <Link
              to="/owner"
              search={{ company: c.company_id }}
              className="mt-4 flex items-center justify-end gap-1 text-sm text-primary opacity-0 group-hover:opacity-100 transition"
            >
              {t.goTo} <ArrowLeft className="w-3 h-3" />
            </Link>
          </div>
        ))}
      </div>

      {/* Explicit totals — labeled as SUM, never blended */}
      <div className="p-5 rounded-xl bg-card border border-border">
        <div className="text-xs uppercase tracking-wide text-muted-foreground mb-3">
          {totalsLabel}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div>
            <div className="text-muted-foreground">{t.wasteLabel}</div>
            <div className="font-bold text-danger">{formatIQD(totals.monthly_waste_iqd)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">{t.opportunityLabel}</div>
            <div className="font-bold text-success">{formatIQD(totals.opportunity_iqd)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">{t.risksLabel}</div>
            <div className="font-bold text-warning">{totals.risk_alerts}</div>
          </div>
          <div>
            <div className="text-muted-foreground">
              {locale === "ar" ? "المستندات" : "بەڵگەنامەکان"}
            </div>
            <div className="font-bold text-primary">{totals.documents_total}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: any;
  label: string;
  value: string;
  sub?: string;
  tone: string;
}) {
  return (
    <div className={`p-3 rounded-lg bg-${tone}/5 border border-${tone}/30`}>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="w-3 h-3" /> {label}
      </div>
      <div className={`text-base font-bold text-${tone} mt-1`}>{value}</div>
      {sub && <div className="text-[10px] text-muted-foreground mt-0.5">{sub}</div>}
    </div>
  );
}
