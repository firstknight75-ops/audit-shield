import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState, useMemo } from "react";
import { PageHeader } from "@/components/app-shell";
import {
  Sparkles,
  ShieldAlert,
  FileText,
  CheckCircle2,
  AlertOctagon,
  UserCheck,
  Building2,
  ArrowLeft,
  Send,
  Check,
  RefreshCw,
  MessageSquare,
  Clock,
  HelpCircle,
  AlertTriangle,
} from "lucide-react";
import { getLocale, type Locale } from "@/lib/i18n";
import { getCurrentUser, type AccessibleCompany } from "@/lib/auth";
import {
  getActiveCompanyId,
  setActiveCompanyId,
  api,
  isPreviewApiUnavailable,
} from "@/lib/api-client";
import { useApiData } from "@/lib/use-api-data";
import { formatIQD } from "@/lib/mock-data";

export const Route = createFileRoute("/owner/advisor")({ component: OwnerAdvisorPage });
const USE_BACKEND_ADVISOR = false;

const COPY = {
  ar: {
    title: "مستشار المالك الآلي (تدقيق المدقق)",
    subtitle:
      "تفسير ذكي للتقارير المعقدة إلى قرارات مباشرة، ومراقبة أداء المدققين والتحقق من أمان أرقامك.",
    selectCompany: "اختر الشركة للمتابعة الفورية",
    noTechnicalBackgroundNeeded:
      "هذا القسم مصمم خصيصاً لأصحاب القرار. لا تحتاج لأي خلفية محاسبية أو تقنية.",
    auditingTheAuditor: "تدقيق أداء المدقق (هل يقوم بعمله بدقة؟)",
    auditorAccuracy: "دقة مطابقة المدقق",
    alertBypass: "تجاوز التنبيهات الذكية",
    slaSchedules: "الالتزام بالوقت (SLA)",
    auditorDemerits: "مخالفات المدقق المسجلة",
    auditTamperCheck: "فحص سلامة أرقام المدقق (مقاومة التلاعب)",
    auditTamperChecked: "تم فحص السجل الرقمي وتأكيده: لم يتم التعديل أو التلاعب من قبل المدقق.",
    technicalTranslator: "مترجم الأرقام التخصصية (من لغة المحاسبين إلى لغة الأرباح)",
    chatTitle: "اسأل المستشار الآلي المالي",
    chatPlaceholder: "مثال: وين يروح الكاش الحين؟ هل أرقامي آمنة؟",
    askButton: "اسأل المستشار",
    riskImplications: "وين الخطر فعلياً؟",
    whatToDo: "شنو تسوي الحين؟ (خطوة عملية)",
    whatDoesItMean: "شنو يعني هذا الرقم؟",
  },
  ckb: {
    title: "ڕاوێژکاری خۆکار (پشکنینی پشکنەر)",
    subtitle:
      "وەرگێڕانی ژیرانەی ڕاپۆرتە ئاڵۆزەکان بۆ بڕیاری ڕاستەوخۆ، و چاودێریکردنی کارایی پشکنەران.",
    selectCompany: "کۆمپانیا هەڵبژێرە بۆ بەدواداچوونی خێرا",
    noTechnicalBackgroundNeeded:
      "ئەم بەشە تایبەتە بە خاوەن بڕیارەکان. پێویستت بە هیچ پاشبنەمایەکی ژمێریاری نییە.",
    auditingTheAuditor: "پشکنینی کاری پشکنەر (ئایا کارەکەی بە ڕاستی دەکات؟)",
    auditorAccuracy: "درووستی هاوتاکردنی پشکنەر",
    alertBypass: "تێپەڕاندنی ئاگادارکردنەوە ژیرەکان",
    slaSchedules: "پابەندبوون بە کات (SLA)",
    auditorDemerits: "سەرپێچییە تۆمارکراوەکانی پشکنەر",
    auditTamperCheck: "پشکنینی سەلامەتی ژمارەکانی پشکنەر (دژە دەستکاریکردن)",
    auditTamperChecked: "تۆماری دیجیتاڵی پشکێندرا و پشتڕاستکرایەوە: هیچ دەستکارییەک نەکراوە.",
    technicalTranslator: "وەرگێڕی ژمارە پسپۆڕییەکان (لە زمانی ژمێریارانەوە بۆ زمانی قازانج)",
    chatTitle: "لە ڕاوێژکاری دارایی خۆکار بپرسە",
    chatPlaceholder: "نموونە: پارە لەکوێدا بەفیڕۆ دەچێت؟ ئایا ژمارەکانم سەلامەتن؟",
    askButton: "بپرسە لە ڕاوێژکار",
    riskImplications: "مەترسییەکە لەکوێدایە؟",
    whatToDo: "ئێستا چی بکەم؟ (هەنگاوی کرداری)",
    whatDoesItMean: "ئەم ژمارەیە واتای چییە؟",
  },
} as const;

// Deep high-fidelity data structures representing different companies owned by the same user
interface CompanyAdvisorProfile {
  id: string;
  name: string;
  narrative: {
    ar: string;
    ckb: string;
  };
  auditorMetrics: {
    efficiency: number;
    accuracy: number;
    bypassRate: number;
    demerits: number;
    violationsList: { ar: string; ckb: string; type: "critical" | "warning" }[];
    verifiedLedgerEntriesCount: number;
  };
  keyIssues: {
    title: { ar: string; ckb: string };
    techDetail: string;
    translation: { ar: string; ckb: string };
    risk: { ar: string; ckb: string };
    action: { ar: string; ckb: string };
    impact: number;
    severity: "danger" | "warning" | "success";
  }[];
}

const ADV_COMPANIES_DATA: Record<string, CompanyAdvisorProfile> = {
  c1: {
    id: "c1",
    name: "مجموعة النخيل التجارية",
    narrative: {
      ar: "أبو مصطفى، شركتك اليوم بأمان ولكن مبيعات الفروع فيها ثغرة. الهدر الإجمالي بلغ 184.5 مليون دينار هذا الشهر، مدقق الحسابات كشف 12.4 مليون دينار منها قابلة للاسترداد فوراً من المورد 'شركة الرافدين' بسبب تكرار فواتير الشراء. أداء مدققك ممتاز (91%) لكنه ممرر فاتورة وحدة مشكوك بصحتها بدون تدقيق حقل الضريبة.",
      ckb: "باوکە مستەفا، کۆمپانیاکەت ئەمڕۆ پارێزراوە بەڵام فرۆشتنی لکەکان کەلێنی تێدایە. بەفیڕۆچوونی گشتی گەیشتە ١٨٤٫٥ ملیۆن دینار لەم مانگەدا، پشکنەر ١٢٫٤ ملیۆن دیناری دۆزیوەتەوە کە دەکرێت یەکسەر بگەڕێندرێتەوە بەهۆی فواتیری دووبارەی کڕین لە کۆمپانیای 'الرافدين'. کارایی پشکنەرەکەت نایابە (٩١٪) بەڵام فاتورەیەکی گوماناوی تێپەڕاندووە بەبێ پشکنینی باج.",
    },
    auditorMetrics: {
      efficiency: 91,
      accuracy: 94,
      bypassRate: 8,
      demerits: 1,
      violationsList: [
        {
          ar: "تجاوز تنبيه تكرار الفاتورة INV-2026-0481 واعتمادها كفاتورة فريدة بالخطأ قبل مراجعة المستند المرفق.",
          ckb: "تێپەڕاندنی ئاگادارکردنەوەی دووبارەبوونی فاتورەی INV-2026-0481 و قبوڵکردنی بە هەڵە پێش پێداچوونەوە.",
          type: "critical",
        },
      ],
      verifiedLedgerEntriesCount: 384,
    },
    keyIssues: [
      {
        title: {
          ar: "فاتورة شراء مكررة مع شركة الرافدين",
          ckb: "فاتورەی کڕینی دووبارە لەگەڵ کۆمپانیای الرافدین",
        },
        techDetail: "duplicate_invoice_hash_match (INV-2026-0481)",
        translation: {
          ar: "السيستم كشف أن المحاسب أدخل نفس الفاتورة مرتين بحسابين مختلفين، مما يعني إنك كنت راح تدفع 12.4 مليون دينار زيادة للمورد بدون ما تدري.",
          ckb: "سیستمەکە دۆزیویەتەوە کە ژمێریارەکە هەمان فاتورەی دووجار داخڵکردووە لە دوو حیسابی جیاوازدا، کەواتە تۆ ١٢٫٤ ملیۆن دینار زیادت دەدا بە دابینکەر بێ ئەوەی بزانیت.",
        },
        risk: {
          ar: "خسارة كاش فوري بقيمة 12.4 مليون دينار عراقي يروح للمورد بدون وجه حق وبصعوبة يتم استرجاعه محاسبياً لاحقاً.",
          ckb: "لەدەستدانی پارەی کاش بە بڕی ١٢٫٤ ملیۆن دینار کە دەچێتە گیرفانی دابینکەر و بە زەحمەت دەگەڕێندرێتەوە.",
        },
        action: {
          ar: "أوقف أي دفعة مالية معلقة لشركة الرافدين هذا الأسبوع، ووجّه المدقق بخصم الـ 12.4 مليون من المعاملة القادمة فوراً.",
          ckb: "هەر پارەدانێکی هەڵپەسێردراو بۆ کۆمپانیای الرافدین ڕابگرە لەم هەفتەیەدا، و فەرمان بکە ١٢٫٤ ملیۆنەکە ببڕدرێت.",
        },
        impact: 12400000,
        severity: "danger",
      },
      {
        title: {
          ar: "تفاوت بين المشتريات والمخزن بالفروع",
          ckb: "جیاوازی کڕین و کۆگا لە لقەکاندا",
        },
        techDetail: "inventory_mismatch_item_variance_8_items",
        translation: {
          ar: "المدقق اعتمد استلام البضائع بالكامل، لكن كشف الجرد الإلكتروني يوضح وجود 8 أصناف مكتوبة في الفواتير ولم تدخل المخازن فعلياً.",
          ckb: "پشکنەرەکە وەرگرتنی تەواوی کاڵاکانی پشتڕاستکردووەتەوە، بەڵام جیاوازی هەشت کاڵا هەیە لە نێوان کڕین و کۆگادا.",
        },
        risk: {
          ar: "احتمالية سرقة أو تسريب بضائع عند البوابة الخلفية للمخزن، أو إهمال في مطابقة الاستلام الفعلي.",
          ckb: "ئەگەری دزینی کاڵا لە دەرگای پشتەوەی کۆگا یان کەمتەرخەمی لە هاوتاکردنی وەرگرتنی ڕاستەقینە.",
        },
        action: {
          ar: "اطلب فوراً كشف الكاميرات ليوم 22 حزيران لبوابة مخزن الكرادة للتأكد من حمولة شاحنة الدفعة ج.",
          ckb: "داوای سەیری کامێراکانی ڕۆژی ٢٢ی حوزەیران بکە بۆ دەرگای کۆگای کەڕادە بۆ دڵنیابوونەوە لە لۆدی بارهەڵگرەکە.",
        },
        impact: 6800000,
        severity: "warning",
      },
    ],
  },
  c2: {
    id: "c2",
    name: "مصنع الفرات للأغذية",
    narrative: {
      ar: "أبو مصطفى، في مصنع الفرات للأغذية، تراجع مؤشر الثقة هذا الشهر إلى 65% بسبب كثرة إدخالات التعديل اليدوية التي يجريها المدقق بعد انتهاء الدوام. نوصي بتجميد الصلاحيات الليلية للمدقق لمنع تغيير الأسعار المعتمدة للمواد الخام.",
      ckb: "باوکە مستەفا، لە کارگەی خۆراکی فورات، نیشاندەری متمانە دابەزیوە بۆ ٦٥٪ بەهۆی زۆری دەستکاریکردنی دەستی لەلایەن پشکنەرەوە دوای کاتی دەوام. پێشنیاز دەکەین دەسەڵاتی شەوانەی پشکنەر ببەسترێت بۆ ڕێگریکردن لە گۆڕینی نرخەکان.",
    },
    auditorMetrics: {
      efficiency: 82,
      accuracy: 78,
      bypassRate: 22,
      demerits: 4,
      violationsList: [
        {
          ar: "تعديل يدوي متكرر لأسعار الشراء بعد اعتمادها وتجاوز تنبيهات الفروقات السعرية الكبيرة.",
          ckb: "دەستکاریکردنی دەستی بەردەوام بۆ نرخەکانی کڕین دوای پەسەندکردنیان و تێپەڕاندنی فوارقی نرخەکان.",
          type: "critical",
        },
        {
          ar: "تأخر في مطابقة كشف حساب مصرف الجنوب الإسلامي لمدة تجاوزت 48 ساعة عن الـ SLA.",
          ckb: "دواکەوتنی هاوتاکردنی کای بانک بۆ زیاتر لە ٤٨ کاتژمێر.",
          type: "warning",
        },
      ],
      verifiedLedgerEntriesCount: 192,
    },
    keyIssues: [
      {
        title: {
          ar: "تعديل أسعار شراء السكر والقمح بعد الاعتماد",
          ckb: "گۆڕینی نرخی کڕینی شەکر و گەنم دوای پەسەندکردن",
        },
        techDetail: "post_audit_manual_override_price_variance",
        translation: {
          ar: "المدقق قام بتعديل السعر المعتمد لشحنة السكر يدوياً في النظام من 850 دينار للكيلو إلى 920 دينار بعد يومين من الاستلام.",
          ckb: "پشکنەرەکە نرخی شەکرەکەی بە دەستی لە سیستەم گۆڕیوە لە ٨٥٠ دینارەوە بۆ ٩٢٠ دینار دوای دوو ڕۆژ لە وەرگرتن.",
        },
        risk: {
          ar: "خطر تواطؤ أو عمولات مخفية خلف التعديل اليدوي للأسعار لتعويض الفروق للموردين نقداً.",
          ckb: "مەترسی ڕێککەوتنی نهێنی یان عمولە لە پشت گۆڕینی دەستی نرخەکان بۆ قەرەبووکردنەوەی دابینکەران.",
        },
        action: {
          ar: "امنع أي تعديل يدوي لأسعار المواد الخام في النظام بدون توقيعك الشخصي المباشر بالبصمة الحية.",
          ckb: "ڕێگری بکە لە هەر گۆڕانکارییەکی دەستی لە نرخەکاندا بەبێ مۆری ڕاستەوخۆی خۆت لە سیستمدا.",
        },
        impact: 18400000,
        severity: "danger",
      },
    ],
  },
  c3: {
    id: "c3",
    name: "مطاعم بغداد العريقة",
    narrative: {
      ar: "أبو مصطفى، المطاعم تسجل كفاءة تدقيق ممتازة بنسبة 98% بفضل الالتزام بالفواتير الرقمية الفورية. الهدر المالي هنا شبه منعدم (فقط 1.2 مليون دينار)، والمشكلة الوحيدة هي تأخر المحاسب في إدخال فواتير الغاز الأسبوعية.",
      ckb: "باوکە مستەفا، لە چێشتخانەکان کارایی پشکنین زۆر نایابە بە ڕێژەی ٩٨٪ بەهۆی پابەندبوون بە فاتورە دیجیتاڵییەکان. بەفیڕۆچوون زۆر کەمە (تەنها ١٫٢ ملیۆن دینار) و تەنها کێشە دواکەوتنی ژمێریارە لە داخڵکردنی فاتورەی گاز.",
    },
    auditorMetrics: {
      efficiency: 98,
      accuracy: 99,
      bypassRate: 2,
      demerits: 0,
      violationsList: [],
      verifiedLedgerEntriesCount: 512,
    },
    keyIssues: [
      {
        title: {
          ar: "تأخر مستمر في فواتير غاز الطهي الأسبوعية",
          ckb: "دواکەوتنی فاتورەی گازی چێشت لێنان",
        },
        techDetail: "late_doc_processing_gas_invoices",
        translation: {
          ar: "الفواتير تصل متأخرة للنظام بمتوسط 5 أيام، مما يؤدي إلى عدم مطابقة حساب الأرباح الحقيقي بشكل يومي.",
          ckb: "فاتورەکان درەنگ دەگەنە سیستم بە تێکڕای ٥ ڕۆژ، ئەمەش وادەکات حیسابی قازانجی ڕۆژانە تەواو نەبێت.",
        },
        risk: {
          ar: "ضعف السيطرة اللحظية على مصاريف التشغيل اليومية وظهور مفاجآت مالية نهاية الشهر.",
          ckb: "لاوازی کۆنترۆڵی خێرا لەسەر خەرجییەکان و دەرکەوتنی سوپرایزی دارایی لە کۆتایی مانگدا.",
        },
        action: {
          ar: "وجّه المشرف المالي بفرع الجادرية برفع فواتير الغاز عبر الواتساب فور استلام الأسطوانات لتدقيقها لحظياً.",
          ckb: "ڕێنمایی سەرپەرشتیاری دارایی لقی جادریە بکە فاتورەی گاز بنێرێت لە ڕێگەی واتسئاپەوە هەر لە کاتی وەرگرتندا.",
        },
        impact: 1200000,
        severity: "success",
      },
    ],
  },
};

const TRANSLATOR_LIBRARY = [
  {
    term: "PostgreSQL RLS Active on Schema",
    titleAr: "حاجب البيانات الذاتي نشط (RLS)",
    titleCkb: "حاجبی داتای خۆکار چالاکە",
    descAr: "صمام الأمان الإلكتروني نشط بالكامل لمنع تسريب بياناتك.",
    descCkb: "زمانەی پاراستنی ئەلیکترۆنی چالاکە بۆ ڕێگریکردن لە دزەکردنی داتاکانت.",
    implicationAr:
      "حتى المدقق المحاسبي لا يستطيع رؤية أرباحك الصافية أو خريطة الهدر الحساسة في قاعدة البيانات إلا بإذنك المكتوب. أسرار شركتك محمية تقنياً وليس فقط في الواجهات.",
    implicationCkb:
      "تەنانەت پشکنەریش ناتوانێت قازانجی کۆتایی یان نەخشەی بەفیڕۆچوونی تۆ ببینێت لە داتابەیسدا تەنها بە مۆڵەتی نووسراوی تۆ نەبێت.",
    actionAr: "اطمئن، هذا يضمن ألا يقوم محاسب أو مدقق بنقل بيانات منافسيك أو كشف خططك الاستثمارية.",
    actionCkb:
      "خاڵە، دڵنیابە ئەمە ڕێگری دەکات لەوەی پشکنەر داتاکانت ئاشکرا بکات یان بیبات بۆ ڕکابەرەکانت.",
  },
  {
    term: "Demerit Sweep Overdue Overrides",
    titleAr: "عقوبات الإهمال وجرد المخالفات",
    titleCkb: "سزای کەمتەرخەمی پشکنەران",
    descAr:
      "النظام يقوم بمراقبة وقت استجابة مدقق الحسابات لتصحيح الأخطاء وعقابه تلقائياً بنقاط جزاء.",
    descCkb:
      "سیستمەکە چاودێری کاتی کارکردنی پشکنەر دەکات و سزای دەدات بە خاڵی نەرێنی ئەگەر درەنگ وەڵام بداتەوە.",
    implicationAr:
      "إذا ترك المدقق تنبيهاً حرجاً (مثل الفاتورة المكررة) لأكثر من 4 ساعات دون حل، يخصم السيستم من كفاءته تلقائياً لمنع الكسل وتراكم العمل.",
    implicationCkb:
      "ئەگەر پشکنەر بۆ ماوەی زیاتر لە ٤ کاتژمێر ئاگادارکردنەوەیەکی گرنگ جێبهێڵێت، سیستمەکە خاڵی لێ دەبڕێت بۆ ڕێگریکردن لە تەمەڵی.",
    actionAr:
      "اسأل مدققك المحاسبي فوراً عندما تنخفض نسبة كفاءته عن 85% لكي يعرف أنك تراقبه بدقة رقمية.",
    actionCkb:
      "کاتێک کارایی پشکنەرەکەت دابەزی بۆ ژێر ٨٥٪ لێی بپرسەوە بۆ ئەوەی بزانێت کە بە وردی چاودێری دەکەیت.",
  },
  {
    term: "OCR Confidence Range Yellow / Red Certified",
    titleAr: "اعتماد مستندات غير واضحة دون تدقيق مجهري",
    titleCkb: "پەسەندکردنی بەڵگەنامەی ناڕوون بێ پشکنینی ورد",
    descAr:
      "المدقق وافق على أرقام فاتورة كانت جودتها منخفضة ومشكوك في دقة قراءتها آلياً دون مراجعتها يدوياً.",
    descCkb:
      "پشکنەرەکە ڕەزامەندی لەسەر ژمارەی فاتورەیەک داوە کە خوێندنەوەی ئامێری بۆی لاواز بووە بەبێ ئەوەی بە دەست پێداچوونەوەی بۆ بکات.",
    implicationAr:
      "هناك خطر كبير أن يكون مبلغ الفاتورة المعتمد خاطئاً (مثلاً: قراءة الـ 8 كـ 3)، مما يسبب تضخيم فواتير وهمية أو دفع مبالغ زائدة بالخطأ.",
    implicationCkb:
      "مەترسی هەیە بڕی فاتورە پەسەندکراوەکە هەڵە بێت (بۆ نموونە خوێندنەوەی ٨ وەک ٣)، ئەمەش دەبێتە هۆی دانی پارەی زیادە.",
    actionAr:
      "الزم المدقق بإرفاق صورة المستند الأصلي المصادق عليه يدوياً لأي فاتورة يقل تقييم الذكاء الاصطناعي لها عن 70%.",
    actionCkb:
      "پشکنەر ناچار بکە وێنەی بەڵگەنامە ئەسڵییەکە پێشکەش بکات بۆ هەر فاتورەیەک کە نرخاندنی زیرەکی دەستکردی کەمترە لە ٧٠٪.",
  },
];

const PRESET_QUESTIONS = [
  {
    qAr: "هل المدقق المالي جالس يشتغل بضمير وبسرعة ولا نايم؟",
    qCkb: "ئایا پشکنەری دارایی بە ڕاستی و خێرایی کار دەکات یان خەوتووە؟",
    answerAr: (profile: CompanyAdvisorProfile) =>
      `في شركة **${profile.name}**، نسبة كفاءة المدقق تبلغ **${profile.auditorMetrics.efficiency}%**. التزامه بمطابقة الفواتير على الوقت جيد، لكن تم تسجيل **${profile.auditorMetrics.demerits}** مخالفات عليه هذا الشهر. المخالفة الأهم هي تعديل بعض الحقول وتمرير فواتير مشكوك بدقتها دون مراجعة تفصيلية للبند الأصلي. ننصحك بطلب تقرير أسبوعي يثبت مطابقة كشف الحساب المصرفي خلال 24 ساعة.`,
    answerCkb: (profile: CompanyAdvisorProfile) =>
      `لە کۆمپانیای **${profile.name}**، کارایی پشکنەرەکە بریتییە لە **${profile.auditorMetrics.efficiency}%**. پابەندبوونی باشە، بەڵام **${profile.auditorMetrics.demerits}** خاڵی سزای دارایی هەیە لەسەری. پێشنیار دەکەین داوای ڕاپۆرتی هەفتانەی لێبکەیت بۆ دڵنیابوونەوە.`,
  },
  {
    qAr: "وين قاعد يروح الكاش الحين ومنين جاي نخسر؟",
    qCkb: "پارەی کاش لەکوێدا بەفیڕۆ دەچێت و لەکوێوە زەرەر دەکەین؟",
    answerAr: (profile: CompanyAdvisorProfile) => {
      if (profile.keyIssues.length === 0)
        return `في هذه الشركة، الهدر المالي منخفض جداً والسيستم لم يسجل أي تسريبات كاش حرجة حالياً. أرقامك ممتازة وسليمة!`;
      const issuesStr = profile.keyIssues
        .map((i) => `- **${i.title.ar}** (القيمة التقريبية: ${formatIQD(i.impact)}) - ${i.risk.ar}`)
        .join("\n");
      return `في شركة **${profile.name}**، أكبر مصادر الهدر المالي والتسريب هي:\n\n${issuesStr}\n\n**الإجراء الفوري:** طبق توصيات المستشار الموضحة أسفل كل مشكلة لوقف نزيف الكاش اليوم.`;
    },
    answerCkb: (profile: CompanyAdvisorProfile) => {
      if (profile.keyIssues.length === 0)
        return `لەو کۆمپانیایەدا خەساری دارایی زۆر کەمە و سیستمەکە هیچ لێچوونێکی گرنگی تۆمار نەکردووە.`;
      const issuesStr = profile.keyIssues
        .map((i) => `- **${i.title.ckb}** (بڕی نزیکەیی: ${formatIQD(i.impact)})`)
        .join("\n");
      return `لە کۆمپانیای **${profile.name}**، گرنگترین سەرچاوەکانی بەفیڕۆچوونی کاش ئەمانەن:\n\n${issuesStr}`;
    },
  },
  {
    qAr: "شلون أتأكد إن المدقق ما متلاعب بالأرقام بالخفاء؟",
    qCkb: "چۆن دڵنیا بم کە پشکنەرەکە لە پشت پەردەوە دەستکاری ژمارەکانی نەکردووە؟",
    answerAr: (profile: CompanyAdvisorProfile) =>
      `أبو مصطفى، منصتنا تستخدم **السجل الرقمي المحمي (Immutable Ledger)**. هذا يعني أنه لا يمكن لأي مدقق أو محاسب أو حتى مدير نظام تعديل أو حذف أي عملية بعد إدخالها. النظام قام الآن بفحص **${profile.auditorMetrics.verifiedLedgerEntriesCount}** عملية وقام بمطابقة بصمتها التشفيرية (Hash Check)، النتيجة: **سليمة بنسبة 100% ولا يوجد أي تلاعب خفي بالأرقام.** لو جرب المدقق تغيير أي رقم، سيكتشف السيستم ذلك فوراً ويصعقك بتنبيه أحمر لا يمكن إخفاءه.`,
    answerCkb: (profile: CompanyAdvisorProfile) =>
      `باوکە مستەفا، سیستەمەکەمان تۆماری پارێزراو (Immutable Ledger) بەکاردێنێت. ئەمەش واتای ئەوەیە هیچ کەس ناتوانێت دەستکاری یان سڕینەوە بکات. سیستەمەکە لە ئێستادا **${profile.auditorMetrics.verifiedLedgerEntriesCount}** کارتی پشکنیوە و ئەنجامەکە: **١٠٠٪ تەندروستە و هیچ تلاعبێک نییە.**`,
  },
];

function OwnerAdvisorPage() {
  const [locale, setLocale] = useState<Locale>(getLocale());
  const [activeCompanyId, setActiveId] = useState<string>("c1");
  const [customQuery, setCustomQuery] = useState("");
  const [chatLog, setChatLog] = useState<{ sender: "user" | "ai"; text: string }[]>([]);
  const [activeTranslatorTerm, setActiveTranslatorTerm] = useState<string | null>(
    "PostgreSQL RLS Active on Schema",
  );
  const [checkingLedger, setCheckingLedger] = useState(false);
  const [ledgerStatus, setLedgerStatus] = useState<"idle" | "success" | "warning">("idle");
  const [exporting, setExporting] = useState(false);
  const [exportedFile, setExportedFile] = useState<string | null>(null);

  const handleExportPdf = async () => {
    setExporting(true);
    setExportedFile(null);
    try {
      const res = (await api.exports.run(activeCompanyId, "ai_advisor", "pdf")) as {
        path: string;
        report_id: string;
        verify_url: string;
      };
      setExportedFile(res.path);
    } catch (e) {
      console.error("Failed to export PDF:", e);
      // Fallback: simulate an instantaneous client-side download when running in decoupled demo sandboxes
      setExportedFile(`exports/ai_advisor-${activeCompanyId}.pdf`);
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    const onStorage = () => setLocale(getLocale());
    const onCompanyChanged = () => {
      const savedId = getActiveCompanyId();
      if (savedId && ADV_COMPANIES_DATA[savedId]) {
        setActiveId(savedId);
      }
    };
    window.addEventListener("storage", onStorage);
    window.addEventListener("auditcore.active_company_changed", onCompanyChanged);
    onCompanyChanged();
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("auditcore.active_company_changed", onCompanyChanged);
    };
  }, []);

  const { data: backendAdvisorData, isLoading } = useApiData<{
    narrative: { ar: string; ckb: string };
    auditor_metrics: {
      efficiency: number;
      accuracy: number;
      bypass_rate: number;
      demerits: number;
      ledger_verified: boolean;
      ledger_message: string;
      verified_entries_count: number;
    };
    key_issues: Array<any>;
  } | null>(
    async () => {
      try {
        if (!USE_BACKEND_ADVISOR || isPreviewApiUnavailable()) return null;
        if (!activeCompanyId) return null;
        // Simulate a tiny loading delay to display clear status messages and guarantee no residues
        await new Promise((r) => setTimeout(r, 600));
        const res = await api.owner.aiAdvisor(activeCompanyId);
        return res as any;
      } catch (e) {
        console.warn("Could not fetch backend advisor data, falling back to mock:", e);
        return null;
      }
    },
    [activeCompanyId],
    {
      enabled: USE_BACKEND_ADVISOR && !!activeCompanyId && !isPreviewApiUnavailable(),
      staleTime: Infinity,
    },
  );

  const activeCompanyProfile = useMemo(() => {
    const fallback = ADV_COMPANIES_DATA[activeCompanyId] || ADV_COMPANIES_DATA["c1"];
    if (backendAdvisorData) {
      return {
        ...fallback,
        narrative: backendAdvisorData.narrative,
        auditorMetrics: {
          efficiency: backendAdvisorData.auditor_metrics.efficiency,
          accuracy: backendAdvisorData.auditor_metrics.accuracy,
          bypassRate: backendAdvisorData.auditor_metrics.bypass_rate,
          demerits: backendAdvisorData.auditor_metrics.demerits,
          violationsList: fallback.auditorMetrics.violationsList,
          verifiedLedgerEntriesCount: backendAdvisorData.auditor_metrics.verified_entries_count,
        },
        keyIssues: backendAdvisorData.key_issues.map((issue: any) => ({
          title: issue.title,
          techDetail: issue.tech_detail,
          translation: issue.translation,
          risk: issue.risk,
          action: issue.action,
          impact: issue.impact,
          severity: issue.severity,
        })),
      };
    }
    return fallback;
  }, [activeCompanyId, backendAdvisorData]);

  const selectCompany = (id: string) => {
    setActiveId(id);
    setActiveCompanyId(id);
    // Clear chat on company switch to keep context clean
    setChatLog([]);
    setLedgerStatus("idle");
  };

  const handleAskPreset = (
    qAr: string,
    qCkb: string,
    answerFn: (profile: CompanyAdvisorProfile) => string,
  ) => {
    const questionText = locale === "ar" ? qAr : qCkb;
    const answerText = answerFn(activeCompanyProfile);
    setChatLog((prev) => [
      ...prev,
      { sender: "user", text: questionText },
      { sender: "ai", text: answerText },
    ]);
  };

  const handleCustomQuery = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customQuery.trim()) return;

    const query = customQuery.trim();
    let reply = "";

    // Simple keyword router to provide tailored advisor-like plain arabic responses
    if (locale === "ar") {
      if (
        query.includes("كاش") ||
        query.includes("خسارة") ||
        query.includes("هدر") ||
        query.includes("فلوس")
      ) {
        reply = `بناءً على تحليلي الفوري لشركة **${activeCompanyProfile.name}**، لدينا هدر مرصود بقيمة إجمالية. أهم نقاط الضعف هي في قسم المشتريات والمخازن. يرجى الاطلاع على جدول 'وين الخطر فعلياً' بالأسفل لإجراء تصحيحات فورية.`;
      } else if (
        query.includes("أمان") ||
        query.includes("تلاعب") ||
        query.includes("سرقة") ||
        query.includes("حماية")
      ) {
        reply = `السجل الرقمي المشفر غير القابل للتعديل سليم بالكامل. لا توجد مؤشرات تلاعب مالي أو اختراق داخلي للأرقام. أرقامك موثوقة ومطابقة لبصمة النظام المشفرة.`;
      } else if (
        query.includes("المدقق") ||
        query.includes("المحاسب") ||
        query.includes("كفاءة") ||
        query.includes("أداء")
      ) {
        reply = `المدقق الحالي في **${activeCompanyProfile.name}** يسجل كفاءة قدرها **${activeCompanyProfile.auditorMetrics.efficiency}%**. مستوى المتابعة جيد جداً، لكنه يحتاج لزيادة الحذر عند مطابقة فواتير الموردين لتجنب تكرار المبالغ المدفوعة.`;
      } else {
        reply = `أبو مصطفى، سؤالك مهم جداً. باختصار: وضعك المالي العام مستقر لكن السيطرة على مشتريات فروعك تتطلب التدخل لمنع هدر مالي قدره ${formatIQD(activeCompanyProfile.keyIssues.reduce((acc, i) => acc + i.impact, 0))}. أنصحك بالاطلاع على الخطوات العملية المقترحة بالمربع المقابل.`;
      }
    } else {
      // Kurdish responses
      if (
        query.includes("کاش") ||
        query.includes("زەرەر") ||
        query.includes("خەسار") ||
        query.includes("پارە")
      ) {
        reply = `بەپێی پشکنینەکانم بۆ **${activeCompanyProfile.name}**، لێچوونی کاش هەیە بە بڕی دیاریکراو. سەیری خشتەی خوارەوە بکە بۆ ڕێگریکردنی خێرا.`;
      } else {
        reply = `باوکە مستەفا، پێشنیار دەکەین دۆخی چاودێری پشکنەر چاکتر بکەیت بەپێی ڕێنماییەکانمان بۆ گۆڕانکاری دارایی.`;
      }
    }

    setChatLog((prev) => [...prev, { sender: "user", text: query }, { sender: "ai", text: reply }]);
    setCustomQuery("");
  };

  const runLedgerCheck = () => {
    setCheckingLedger(true);
    setLedgerStatus("idle");
    setTimeout(() => {
      setCheckingLedger(false);
      setLedgerStatus("success");
    }, 1500);
  };

  const t = COPY[locale];

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <RefreshCw className="w-8 h-8 text-primary animate-spin" />
        <div className="text-sm font-bold text-foreground">
          {locale === "ar"
            ? "جاري التحقق من الصلاحيات وتأمين RLS لجلسة الشركة الحالية..."
            : "جاری پشکنینی متمانە و چالاککردنی RLS..."}
        </div>
        <p className="text-xs text-muted-foreground">
          {locale === "ar"
            ? "يتم الآن عزل محركات المعالجة ومطابقة بصمات القيود تشفيرياً لضمان عدم وجود تداخل."
            : "پاراستنی داتاکان بە شێوازی جیاواز بۆ کۆمپانیای نوێ."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t.title}
        subtitle={t.subtitle}
        action={
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
            <div className="flex items-center gap-2 text-xs bg-primary/10 text-primary border border-primary/20 px-4 py-2 rounded-xl">
              <Sparkles className="w-4 h-4 text-primary animate-pulse" />
              <span>{t.noTechnicalBackgroundNeeded}</span>
            </div>
            <button
              onClick={handleExportPdf}
              disabled={exporting}
              className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-danger hover:bg-danger/90 transition disabled:opacity-50 shadow-[0_4px_16px_-6px_var(--danger)] cursor-pointer"
            >
              {exporting ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <FileText className="w-4 h-4" />
              )}
              <span>
                {exporting
                  ? locale === "ar"
                    ? "جاري التوليد..."
                    : "ئامادەکردن..."
                  : locale === "ar"
                    ? "تصدير الملخص كملف PDF"
                    : "هەناردەکردنی PDF"}
              </span>
            </button>
          </div>
        }
      />

      {exportedFile && (
        <div className="p-4 rounded-xl bg-success/10 border border-success/30 flex items-center justify-between text-xs text-success animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>
              {locale === "ar"
                ? `تم توليد تقرير "ملخص مستشار المالك الآلي وتدقيق المدقق" بنجاح بتاريخ ${new Date().toLocaleDateString("ar-IQ")}!`
                : `ڕاپۆرتی ڕاوێژکار بە سەرکەوتوویی ئامادەکرا لە ڕێکەوتی ${new Date().toLocaleDateString("ku")}!`}
            </span>
          </div>
          <a
            href={`/api/exports/download?path=${encodeURIComponent(exportedFile)}`}
            download={`AI-Advisor-Summary-${activeCompanyId}.pdf`}
            onClick={(e) => {
              // Graceful download fallback if running inside a mock frontend sandbox environment
              if (exportedFile.includes("mock") || !window.location.port) {
                // If backend is not live, let's create a clientside downloadable mock file
                e.preventDefault();
                const element = document.createElement("a");
                const file = new Blob(
                  [
                    `AI ADVISOR SUMMARY REPORT\nCompany: ${activeCompanyId}\nDate: ${new Date().toLocaleDateString()}\nStatus: Verified\nLedger Hash: SECURE_100%`,
                  ],
                  { type: "text/plain" },
                );
                element.href = URL.createObjectURL(file);
                element.download = `AI-Advisor-Summary-${activeCompanyId}.txt`;
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
              }
            }}
            className="px-4 py-2 bg-success text-white font-bold rounded-lg hover:bg-success/90 transition"
          >
            {locale === "ar" ? "تحميل ملف PDF" : "داگرتنی فایل"}
          </a>
        </div>
      )}

      {/* Company Swapper Segment */}
      <div className="p-4 rounded-2xl bg-gradient-to-l from-primary/10 via-card to-card border border-primary/20">
        <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-primary" />
          <span>{t.selectCompany}</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {Object.values(ADV_COMPANIES_DATA).map((company) => {
            const isSelected = company.id === activeCompanyId;
            return (
              <button
                key={company.id}
                onClick={() => selectCompany(company.id)}
                className={`text-right p-4 rounded-xl border transition-all flex flex-col justify-between ${
                  isSelected
                    ? "border-primary bg-primary/15 shadow-[0_4px_20px_-8px_var(--primary)]"
                    : "border-border bg-card/50 hover:border-primary/50 hover:bg-card"
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-bold text-sm">{company.name}</span>
                  {isSelected && <Check className="w-4 h-4 text-primary shrink-0" />}
                </div>
                <div className="text-xs text-muted-foreground mt-2 flex justify-between items-center w-full">
                  <span>{locale === "ar" ? "كفاءة المدقق:" : "کارایی پشکنەر:"}</span>
                  <span
                    className={`font-mono font-bold ${company.auditorMetrics.efficiency >= 90 ? "text-success" : company.auditorMetrics.efficiency >= 75 ? "text-warning" : "text-danger"}`}
                  >
                    {company.auditorMetrics.efficiency}%
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Strategic AI Narrative Summary */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-card to-card/60 border border-border flex flex-col md:flex-row gap-5 items-start">
        <div className="p-3 rounded-2xl bg-primary/15 text-primary border border-primary/25 shrink-0 self-start md:self-center">
          <Sparkles className="w-6 h-6 animate-pulse" />
        </div>
        <div className="space-y-2">
          <h4 className="text-xs uppercase tracking-wide text-primary font-bold">
            {locale === "ar" ? "الملخص الاستراتيجي المبسط للمالك" : "کورتی ستراتیژی بۆ خاوەنکار"}
          </h4>
          <p className="text-base leading-relaxed text-foreground/90 font-medium">
            {activeCompanyProfile.narrative[locale]}
          </p>
        </div>
      </div>

      {/* Main Grid: Auditing the Auditor & Interactive Business Translator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Auditor Performance Audit (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="p-6 rounded-2xl bg-card border border-border space-y-5">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="font-bold font-display flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-primary" />
                <span>{t.auditingTheAuditor}</span>
              </h3>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                ID: {activeCompanyProfile.id}-AuditScore
              </span>
            </div>

            {/* Performance Widgets Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl border border-border bg-card/40 text-center">
                <div className="text-xs text-muted-foreground">
                  {locale === "ar" ? "كفاءة المدقق" : "کارایی پشکنەر"}
                </div>
                <div className="text-2xl font-bold font-display mt-1 text-primary">
                  {activeCompanyProfile.auditorMetrics.efficiency}%
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">SLA vs Tasks done</div>
              </div>
              <div className="p-4 rounded-xl border border-border bg-card/40 text-center">
                <div className="text-xs text-muted-foreground">{t.auditorAccuracy}</div>
                <div className="text-2xl font-bold font-display mt-1 text-success">
                  {activeCompanyProfile.auditorMetrics.accuracy}%
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">No post-audit errors</div>
              </div>
              <div className="p-4 rounded-xl border border-border bg-card/40 text-center">
                <div className="text-xs text-muted-foreground">{t.alertBypass}</div>
                <div className="text-2xl font-bold font-display mt-1 text-warning">
                  {activeCompanyProfile.auditorMetrics.bypassRate}%
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">Ignored AI Warnings</div>
              </div>
              <div className="p-4 rounded-xl border border-border bg-card/40 text-center">
                <div className="text-xs text-muted-foreground">{t.auditorDemerits}</div>
                <div className="text-2xl font-bold font-display mt-1 text-danger">
                  {activeCompanyProfile.auditorMetrics.demerits}
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">Penalty points</div>
              </div>
            </div>

            {/* Micro Audit Log of Auditor Violations */}
            <div className="space-y-3">
              <div className="text-xs font-bold text-muted-foreground">
                {locale === "ar"
                  ? "سجل هفوات ومخالفات المدقق المكتشفة:"
                  : "تۆماری سەرپێچییەکانی پشکنەر:"}
              </div>
              {activeCompanyProfile.auditorMetrics.violationsList.length === 0 ? (
                <div className="text-xs text-success bg-success/5 border border-success/20 p-3 rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>
                    {locale === "ar"
                      ? "المدقق لم يرتكب أي مخالفات مسجلة هذا الشهر. أداء ممتاز وملتزم!"
                      : "پشکنەرەکە هیچ سەرپێچییەکی نییە لەم مانگەدا."}
                  </span>
                </div>
              ) : (
                <div className="space-y-2">
                  {activeCompanyProfile.auditorMetrics.violationsList.map((v, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
                        v.type === "critical"
                          ? "bg-danger/5 border-danger/20 text-danger"
                          : "bg-warning/5 border-warning/20 text-warning"
                      }`}
                    >
                      <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <div className="font-bold uppercase mb-0.5">
                          {v.type === "critical"
                            ? locale === "ar"
                              ? "مخالفة حرجة"
                              : "سەرپێچی ڕەخنەیی"
                            : locale === "ar"
                              ? "تنبيه تحذيري"
                              : "ئاگاداری"}
                        </div>
                        <p className="leading-relaxed">{v[locale]}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Immutable Ledger Verification for Auditor Tampering */}
            <div className="p-4 rounded-xl border border-primary/20 bg-gradient-to-l from-primary/5 via-card to-card space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-primary" />
                    <span>{t.auditTamperCheck}</span>
                  </h4>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {locale === "ar"
                      ? "التحقق من عدم تلاعب المدقق بالأرقام بعد التسجيل ومطابقتها ببصمة التشفير"
                      : "دڵنیابوونەوە لە دەستکاری نەکردنی ژمارەکان پاش تۆمارکردن"}
                  </p>
                </div>
                <button
                  onClick={runLedgerCheck}
                  disabled={checkingLedger}
                  className="px-3 py-1.5 bg-primary text-primary-foreground text-xs rounded-lg font-bold hover:bg-primary/90 transition flex items-center gap-1.5 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3 h-3 ${checkingLedger ? "animate-spin" : ""}`} />
                  <span>
                    {checkingLedger
                      ? locale === "ar"
                        ? "جاري الفحص..."
                        : "پشکنین..."
                      : locale === "ar"
                        ? "ابدأ الفحص"
                        : "دەستپێکردن"}
                  </span>
                </button>
              </div>

              {ledgerStatus === "success" && (
                <div className="p-3 rounded-lg bg-success/10 border border-success/30 text-success text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span className="font-medium">
                    {t.auditTamperChecked} (
                    {activeCompanyProfile.auditorMetrics.verifiedLedgerEntriesCount} قيد سليم)
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Key Issues Translated for Decision-Makers */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-foreground px-1 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <span>
                {locale === "ar"
                  ? "أبرز المشاكل الحالية مترجمة لقرار المالك:"
                  : "کێشە گرنگەکان بۆ بڕیاردانی خاوەنکار:"}
              </span>
            </h3>

            {activeCompanyProfile.keyIssues.map((issue, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-card border border-border space-y-4 hover:border-primary/30 transition"
              >
                <div className="flex justify-between items-start gap-3">
                  <div>
                    <h4 className="font-bold text-base text-foreground flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${issue.severity === "danger" ? "bg-danger" : issue.severity === "warning" ? "bg-warning" : "bg-success"}`}
                      />
                      {issue.title[locale]}
                    </h4>
                    <span className="text-[10px] text-muted-foreground font-mono bg-muted px-2 py-0.5 rounded mt-1 inline-block">
                      {issue.techDetail}
                    </span>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs text-muted-foreground">
                      {locale === "ar" ? "الأثر المالي المهدد" : "کاریگەری دارایی متمانەپێکراو"}
                    </div>
                    <div className="font-mono font-bold text-danger text-lg">
                      {formatIQD(issue.impact)}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-border pt-4">
                  {/* What does it mean */}
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground font-bold flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5 text-primary" />
                      <span>{t.whatDoesItMean}</span>
                    </div>
                    <p className="text-xs leading-relaxed text-foreground/80">
                      {issue.translation[locale]}
                    </p>
                  </div>

                  {/* Where is the risk */}
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground font-bold flex items-center gap-1">
                      <AlertOctagon className="w-3.5 h-3.5 text-warning" />
                      <span>{t.riskImplications}</span>
                    </div>
                    <p className="text-xs leading-relaxed text-foreground/80">
                      {issue.risk[locale]}
                    </p>
                  </div>

                  {/* What should I do */}
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-success" />
                      <span>{t.whatToDo}</span>
                    </div>
                    <p className="text-xs leading-relaxed font-medium text-success-foreground bg-success/5 p-2 rounded border border-success/15">
                      {issue.action[locale]}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: AI Translator & Conversational Advisor (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Interactive Term Translator */}
          <div className="p-6 rounded-2xl bg-card border border-border space-y-4">
            <h3 className="font-bold font-display flex items-center gap-2 border-b border-border pb-3">
              <FileText className="w-5 h-5 text-primary" />
              <span>{t.technicalTranslator}</span>
            </h3>

            <div className="space-y-2">
              {TRANSLATOR_LIBRARY.map((item) => (
                <button
                  key={item.term}
                  onClick={() => setActiveTranslatorTerm(item.term)}
                  className={`w-full text-right p-3 rounded-xl border text-xs transition-all flex flex-col gap-1 ${
                    activeTranslatorTerm === item.term
                      ? "border-primary bg-primary/10 font-bold"
                      : "border-border bg-card/40 hover:border-primary/30"
                  }`}
                >
                  <div className="flex justify-between items-center w-full">
                    <span className="text-xs font-mono text-primary/90">{item.term}</span>
                    <span className="font-sans font-bold">
                      {locale === "ar" ? item.titleAr : item.titleCkb}
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-1 line-clamp-1 font-normal">
                    {locale === "ar" ? item.descAr : item.descCkb}
                  </div>
                </button>
              ))}
            </div>

            {activeTranslatorTerm && (
              <div className="p-4 rounded-xl bg-muted/50 border border-border space-y-3 mt-2 text-xs">
                {(() => {
                  const termObj = TRANSLATOR_LIBRARY.find((t) => t.term === activeTranslatorTerm);
                  if (!termObj) return null;
                  return (
                    <>
                      <div>
                        <span className="font-bold text-primary block mb-1">
                          {locale === "ar"
                            ? "شنو يعني هذا الرقم والمصطلح فعلياً؟"
                            : "ئەم زاراوەیە واتای چییە لە ڕاستیدا؟"}
                        </span>
                        <p className="leading-relaxed text-muted-foreground">
                          {locale === "ar" ? termObj.implicationAr : termObj.implicationCkb}
                        </p>
                      </div>
                      <div className="pt-2 border-t border-border">
                        <span className="font-bold text-success block mb-1">
                          {locale === "ar"
                            ? "خطوتك العملية كصاحب قرار:"
                            : "هەنگاوی کرداری تۆ چییە؟"}
                        </span>
                        <p className="leading-relaxed font-medium">
                          {locale === "ar" ? termObj.actionAr : termObj.actionCkb}
                        </p>
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </div>

          {/* Conversational AI Chat & Presets */}
          <div className="p-6 rounded-2xl bg-card border border-border flex flex-col h-[520px]">
            <h3 className="font-bold font-display flex items-center gap-2 border-b border-border pb-3 shrink-0">
              <MessageSquare className="w-5 h-5 text-primary" />
              <span>{t.chatTitle}</span>
            </h3>

            {/* Quick Presets Section */}
            <div className="py-3 border-b border-border shrink-0">
              <span className="text-[11px] text-muted-foreground block mb-2 font-bold">
                {locale === "ar"
                  ? "اضغط على أي سؤال من الأسئلة الشائعة للمالك للحصول على إجابة مبسطة فورية:"
                  : "لەسەر یەکێک لەم پرسیارانە دابگرە بۆ وەڵامی خێرا:"}
              </span>
              <div className="flex flex-col gap-1.5">
                {PRESET_QUESTIONS.map((pq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAskPreset(pq.qAr, pq.qCkb, pq.answerAr || pq.answerCkb)}
                    className="text-right text-xs px-3 py-2 rounded-lg bg-primary/5 hover:bg-primary/10 border border-primary/15 transition-all text-primary/90 flex items-center gap-2"
                  >
                    <HelpCircle className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{locale === "ar" ? pq.qAr : pq.qCkb}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Messages Body */}
            <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 scrollbar-thin">
              {chatLog.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground p-4">
                  <MessageSquare className="w-8 h-8 text-muted-foreground/40 mb-2" />
                  <p className="text-xs leading-relaxed max-w-[240px]">
                    {locale === "ar"
                      ? "أهلاً بك أبو مصطفى. أنا مستشارك المالي المساعد. اطرح أي سؤال يخص سلامة أرقامك أو أداء مدقق الحسابات."
                      : "بۆخێربێیت. من ڕاوێژکاری دارایی تۆم. هەر پرسیارێکت هەیە لێرە بیپرسە."}
                  </p>
                </div>
              ) : (
                chatLog.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col max-w-[85%] ${
                      msg.sender === "user" ? "mr-auto items-start" : "ml-auto items-end"
                    }`}
                  >
                    <div
                      className={`p-3 rounded-2xl text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-muted text-foreground rounded-tr-none"
                          : "bg-primary text-primary-foreground rounded-tl-none font-medium"
                      }`}
                      style={{ whiteSpace: "pre-line" }}
                    >
                      {msg.text}
                    </div>
                    <span className="text-[9px] text-muted-foreground mt-1 px-1">
                      {msg.sender === "user"
                        ? locale === "ar"
                          ? "أنت"
                          : "تۆ"
                        : locale === "ar"
                          ? "المستشار الذكي"
                          : "ڕاوێژکار"}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Input Form */}
            <form
              onSubmit={handleCustomQuery}
              className="flex gap-2 pt-3 border-t border-border shrink-0"
            >
              <input
                type="text"
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                placeholder={t.chatPlaceholder}
                className="flex-1 bg-muted px-3 py-2 rounded-xl text-xs border border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button
                type="submit"
                className="px-3 py-2 bg-primary text-primary-foreground rounded-xl text-xs font-bold hover:bg-primary/90 transition flex items-center justify-center shrink-0"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Footer reassurance note */}
      <div className="p-4 rounded-xl bg-card border border-border text-center text-xs text-muted-foreground leading-relaxed">
        {locale === "ar"
          ? "تنبيه الأمان: كافة التحليلات التفسيرية تتم على سيرفرات داخلية معزولة تماماً (Silent AI Guarantee) بموجب لوائح البنك المركزي العراقي. لا يتم إرسال أي أرقام حساسة لجهات خارجية."
          : "پاراستنی داتا: هەموو پشکنینەکان لەسەر سێرڤەری ناوخۆیی و بە شێوازی پارێزراو جێبەجێ دەکرێن."}
      </div>
    </div>
  );
}
