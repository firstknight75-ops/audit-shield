import { useState } from "react";
import { ShieldCheck, Clock, FileCheck2, Lock, Sparkles } from "lucide-react";
import { type Locale } from "@/lib/i18n";

/**
 * AuditorOnboarding — the trust-framing card.
 *
 * Shown to the Auditor on first login AND at the top of the certification
 * screen. States plainly and warmly that the Auditor is the most
 * operationally trusted role in the system (90%), and that the restriction
 * on seeing analytical conclusions protects the integrity of their own
 * work — so their input can never be shaped by knowing what it will
 * reveal — rather than reflecting any distrust of them personally.
 *
 * Both languages are first-class. No mixed-language fallback.
 */

const COPY = {
  ar: {
    greeting: "أهلاً بك في فريق التدقيق",
    headline: "أنت الدور الأكثر ثقة تشغيلاً في هذا النظام",
    trustPct: "٪90 من الثقة التشغيلية",
    why: "لماذا لا أرى التحليلات؟",
    explanation:
      "عدم رؤيتك للتحليلات المالية لا ينبع من أي شك فيك شخصياً — بل العكس تماماً: لأن مدخلاتك يجب ألا تتأثر بمعرفة ما ستكشفه لاحقاً. هذا يحمي نزاهة عملك أنت.",
    training: "هدف التدريب: أقل من 30 دقيقة لتصبح جاهزاً.",
    noAuto: "لا يتم اعتماد أي مستند تلقائياً — كل نتيجة OCR تنتظر مراجعتك وتصحيحك.",
    irreversible: "كل اعتماد يُسجَّل في سلسلة غير قابلة للتعديل. عملك محفوظ إلى الأبد.",
    dismiss: "فهمت، لن يظهر مرة أخرى",
  },
  ckb: {
    greeting: "بەخێربێیت بۆ تیمی پشکنین",
    headline: "تۆ متمانەپێوترین ڕۆڵی کارپێکردن لەم سیستەمەدا",
    trustPct: "٪٩٠ متمانەی کارپێکردن",
    why: "بۆچی شیکارییەکان نابینم؟",
    explanation:
      "ئەوەی تۆ شیکاری دارایییەکان نابینیت لە هیچ دوودڵییەکی تایبەت بە تۆوە سەرچاوە ناگرێت — بەڵکو بە پێچەوانە: چونکە داتاکانی تۆ نابێت کار لەسەر زانینی ئەوەی دواتر ئاشکرا دەبێت بکەن. ئەمە دەستپاکی کاری تۆ دەپارێزێت.",
    training: "ئامانجی ڕاهێنان: کەمتر لە ٣٠ خولەک بۆ ئامادەبوون.",
    noAuto:
      "هیچ بەڵگەنامەیەک بە خۆکار پەسند ناکرێت — هەموو ئەنجامی OCR چاوەڕێ پێداچوونەوە و ڕاستکردنەوەی تۆ دەکات.",
    irreversible:
      "هەموو پەسندکردنێک لە زنجیرەیەکی نەگۆڕاو تۆمار دەکرێت. کاری تۆ بۆ هەمیشە پارێزراوە.",
    dismiss: "تێگەیشتم، دووبارە نادەردەکرێتەوە",
  },
} as const;

const STORAGE_KEY = "auditcore.auditor.onboarding.dismissed.v1";

export function AuditorOnboarding({ locale, force = false }: { locale: Locale; force?: boolean }) {
  const t = COPY[locale];
  const [dismissed, setDismissed] = useState(() => {
    if (force) return false;
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem(STORAGE_KEY) === "1";
  });
  if (dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, "1");
    }
  };

  return (
    <div className="mb-6 p-6 rounded-2xl bg-gradient-to-br from-primary/10 via-success/5 to-primary/5 border border-primary/30 relative overflow-hidden">
      <div className="absolute top-0 end-0 w-32 h-32 rounded-full bg-primary/10 blur-2xl" />
      <div className="relative">
        <div className="flex items-start gap-3 mb-4">
          <div className="p-3 rounded-xl bg-primary/15 text-primary border border-primary/30">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="text-xs text-muted-foreground">{t.greeting}</div>
            <h2 className="text-xl font-bold mt-1 leading-snug">{t.headline}</h2>
            <div className="inline-flex items-center gap-1 mt-2 px-3 py-1 rounded-full bg-success/15 text-success border border-success/30 text-sm font-bold">
              <Sparkles className="w-3 h-3" /> {t.trustPct}
            </div>
          </div>
        </div>

        <div className="bg-card/60 backdrop-blur rounded-xl p-4 border border-border/50 mb-4">
          <h3 className="font-bold text-sm flex items-center gap-2 mb-2">
            <Lock className="w-4 h-4 text-primary" /> {t.why}
          </h3>
          <p className="text-sm leading-relaxed text-foreground/90">{t.explanation}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div className="p-3 rounded-lg bg-card/60 border border-border/50">
            <div className="flex items-center gap-2 text-xs font-bold mb-1">
              <Clock className="w-3 h-3 text-primary" /> {t.training}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-card/60 border border-border/50">
            <div className="flex items-center gap-2 text-xs font-bold mb-1">
              <FileCheck2 className="w-3 h-3 text-warning" /> {t.noAuto}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-card/60 border border-border/50">
            <div className="flex items-center gap-2 text-xs font-bold mb-1">
              <ShieldCheck className="w-3 h-3 text-success" /> {t.irreversible}
            </div>
          </div>
        </div>

        <button
          onClick={handleDismiss}
          className="w-full md:w-auto px-6 py-2 rounded-md bg-primary text-primary-foreground text-sm font-bold hover:opacity-90 transition"
        >
          {t.dismiss}
        </button>
      </div>
    </div>
  );
}
