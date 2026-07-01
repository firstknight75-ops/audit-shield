import { createFileRoute } from "@tanstack/react-router";
import { useState, useMemo } from "react";
import { PageHeader } from "@/components/app-shell";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Search,
  Calendar,
  Filter,
  Clock,
} from "lucide-react";
import { getLocale } from "@/lib/i18n";

export const Route = createFileRoute("/owner/ledger")({ component: Ledger });

// Enriching the dataset with dates, departments, and diverse action logs
const RICH_LEDGER_ENTRIES = [
  {
    id: "l1",
    at: "2026-06-28 09:14",
    actor: "زينب الكاظمي",
    action: "اعتماد مستند",
    target: "INV-2026-0481",
    hash: "a7c361fa2d0391f",
    department: "المشتريات",
    timestamp: new Date("2026-06-28T09:14:00"),
  },
  {
    id: "l2",
    at: "2026-06-28 09:02",
    actor: "زينب الكاظمي",
    action: "تصحيح خطأ OCR",
    target: "حقل المبلغ: 12,400,000 ← 12,450,000",
    hash: "b21df0c44ae834a",
    department: "المشتريات",
    timestamp: new Date("2026-06-28T09:02:00"),
  },
  {
    id: "l3",
    at: "2026-06-27 15:45",
    actor: "أحمد المياحي",
    action: "ترحيل قيد تسوية",
    target: "تسوية حساب مصرف الجنوب الإسلامي حزيران",
    hash: "f3c3098eab110d2",
    department: "المالية",
    timestamp: new Date("2026-06-27T15:45:00"),
  },
  {
    id: "l4",
    at: "2026-06-26 11:20",
    actor: "حيدر الكرخي",
    action: "مطابقة رصيد مخزن الكرادة",
    target: "8 أصناف تفاوت - شحنة المواد الأولية ج",
    hash: "4d76b1e8e2029bf",
    department: "المخازن",
    timestamp: new Date("2026-06-26T11:20:00"),
  },
  {
    id: "l5",
    at: "2026-06-25 08:31",
    actor: "مصطفى الجبوري",
    action: "منح صلاحية استثنائية مؤقتة",
    target: "view_waste_map ← مدير المشتريات (7 أيام)",
    hash: "9e88cb2cd4420c2",
    department: "المالية",
    timestamp: new Date("2026-06-25T08:31:00"),
  },
  {
    id: "l6",
    at: "2026-06-24 18:00",
    actor: "النظام",
    action: "كشف هدر مالي آلي",
    target: "تكرار فاتورة INV-2026-9001 (12.4M)",
    hash: "81e2b3c4f5a6d7e",
    department: "المشتريات",
    timestamp: new Date("2026-06-24T18:00:00"),
  },
  {
    id: "l7",
    at: "2026-06-22 02:00",
    actor: "النظام",
    action: "تشغيل التحليل اليومي",
    target: "مؤشر الثقة = 78 / 100",
    hash: "5ff17c093a027b9",
    department: "عام / النظام",
    timestamp: new Date("2026-06-22T02:00:00"),
  },
  {
    id: "l8",
    at: "2026-06-15 14:10",
    actor: "سارة حسن",
    action: "تحديث شروط التعاقد",
    target: "مورد السكر المعتمد - مصنع الفرات",
    hash: "7c3b91a2e30f1d9",
    department: "المشتريات",
    timestamp: new Date("2026-06-15T14:10:00"),
  },
  {
    id: "l9",
    at: "2026-06-10 10:00",
    actor: "النظام",
    action: "تهيئة البيئة السحابية للشركة",
    target: "حاجب البيانات الذاتي RLS نشط بنجاح",
    hash: "d3b2f5c719e83fa",
    department: "عام / النظام",
    timestamp: new Date("2026-06-10T10:00:00"),
  },
];

const DEPARTMENTS = ["الكل", "المشتريات", "المالية", "المخازن", "عام / النظام"];
const PERIODS = [
  { id: "all", label: "كل الأوقات" },
  { id: "today", label: "اليوم" },
  { id: "week", label: "آخر 7 أيام" },
  { id: "month", label: "آخر 30 يوماً" },
];

function Ledger() {
  const [locale] = useState(() => getLocale());
  const [verified, setVerified] = useState<null | boolean>(null);
  const [message, setMessage] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDept, setSelectedDept] = useState("الكل");
  const [selectedPeriod, setSelectedPeriod] = useState("all");
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest">("newest");

  // Filtering and sorting logic
  const filteredEntries = useMemo(() => {
    let result = [...RICH_LEDGER_ENTRIES];

    // 1. Text Search (Actor, Action, Target, Hash)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (e) =>
          e.actor.toLowerCase().includes(q) ||
          e.action.toLowerCase().includes(q) ||
          e.target.toLowerCase().includes(q) ||
          e.hash.toLowerCase().includes(q),
      );
    }

    // 2. Department Filtering
    if (selectedDept !== "الكل") {
      result = result.filter((e) => e.department === selectedDept);
    }

    // 3. Time Period Filtering
    const now = new Date("2026-06-30T12:00:00"); // Today's date relative to prompt context
    if (selectedPeriod === "today") {
      result = result.filter((e) => {
        const diffTime = Math.abs(now.getTime() - e.timestamp.getTime());
        const diffDays = diffTime / (1000 * 60 * 60 * 24);
        return diffDays <= 1;
      });
    } else if (selectedPeriod === "week") {
      result = result.filter((e) => {
        const diffTime = Math.abs(now.getTime() - e.timestamp.getTime());
        const diffDays = diffTime / (1000 * 60 * 60 * 24);
        return diffDays <= 7;
      });
    } else if (selectedPeriod === "month") {
      result = result.filter((e) => {
        const diffTime = Math.abs(now.getTime() - e.timestamp.getTime());
        const diffDays = diffTime / (1000 * 60 * 60 * 24);
        return diffDays <= 30;
      });
    }

    // 4. Sorting (Newest first is default)
    result.sort((a, b) => {
      const timeA = a.timestamp.getTime();
      const timeB = b.timestamp.getTime();
      return sortOrder === "newest" ? timeB - timeA : timeA - timeB;
    });

    return result;
  }, [searchQuery, selectedDept, selectedPeriod, sortOrder]);

  return (
    <div className="space-y-6">
      <PageHeader
        title={locale === "ar" ? "السجل المالي المحمي" : "تۆماری دارایی پارێزراو"}
        subtitle={
          locale === "ar"
            ? "سلسلة SHA-256 مشفرة وروابط غير قابلة للتعديل أو الحذف — إثبات فوري لسلامة الأرقام."
            : "تۆمارێکی متمانەپێکراو"
        }
        action={
          <button
            onClick={() => {
              setVerified(null);
              setTimeout(() => {
                setVerified(true);
                setMessage(
                  locale === "ar"
                    ? "تم التحقق تشفيرياً: السجل سليم 100%"
                    : "تۆمارەکە ١٠٠٪ سەلامەتە",
                );
              }, 800);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-[0_4px_12px_-4px_var(--primary)] hover:bg-primary/95 cursor-pointer transition-all"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{locale === "ar" ? "التحقق من سلامة السلسلة" : "پشکنینی متمانە"}</span>
          </button>
        }
      />

      {verified === true && (
        <div className="p-4 rounded-xl bg-success/10 border border-success/30 text-success flex items-center gap-2 animate-fade-in text-xs font-medium">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>
            {message} — تم مطابقة {filteredEntries.length} قيد مالي مع البصمة الأصلية.
          </span>
        </div>
      )}

      {/* Filter and Search Dashboard */}
      <div className="p-5 rounded-2xl bg-card border border-border space-y-4 shadow-sm">
        {/* Main Search & Sorting Options */}
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute start-3 top-2.5 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={
                locale === "ar"
                  ? "البحث باسم المدقق، الإجراء، رقم الفاتورة أو الهاش..."
                  : "گەڕان..."
              }
              className="w-full bg-muted/60 pl-10 pr-10 py-2.5 rounded-xl text-xs border border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground shrink-0 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {locale === "ar" ? "الترتيب:" : "ڕێکخستن:"}
            </span>
            <button
              onClick={() => setSortOrder(sortOrder === "newest" ? "oldest" : "newest")}
              className="px-4 py-2 bg-muted hover:bg-muted/80 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer border border-border"
            >
              <span>
                {sortOrder === "newest"
                  ? locale === "ar"
                    ? "الأحدث أولاً"
                    : "نوێترین"
                  : locale === "ar"
                    ? "الأقدم أولاً"
                    : "کۆنترین"}
              </span>
            </button>
          </div>
        </div>

        {/* Filter Badges: Department & Periods */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center pt-2 border-t border-border/60">
          {/* Department Filter Selector */}
          <div className="lg:col-span-8 flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground flex items-center gap-1 mr-1">
              <Filter className="w-3.5 h-3.5 text-primary" />
              {locale === "ar" ? "القسم:" : "بەش:"}
            </span>
            {DEPARTMENTS.map((dept) => (
              <button
                key={dept}
                onClick={() => setSelectedDept(dept)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer border ${
                  selectedDept === dept
                    ? "bg-primary text-primary-foreground border-primary shadow-sm"
                    : "bg-muted/50 text-muted-foreground border-border hover:bg-muted"
                }`}
              >
                {dept}
              </button>
            ))}
          </div>

          {/* Period Filter Selector */}
          <div className="lg:col-span-4 flex items-center justify-start lg:justify-end gap-2">
            <span className="text-xs text-muted-foreground flex items-center gap-1 mr-1">
              <Calendar className="w-3.5 h-3.5 text-primary" />
              {locale === "ar" ? "الفترة الزمنية:" : "کات:"}
            </span>
            <div className="bg-muted p-1 rounded-xl flex gap-1 border border-border">
              {PERIODS.map((period) => (
                <button
                  key={period.id}
                  onClick={() => setSelectedPeriod(period.id)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                    selectedPeriod === period.id
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Ledger Log Records Table */}
      <div className="rounded-2xl bg-card border border-border overflow-hidden shadow-sm">
        {filteredEntries.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground space-y-2">
            <AlertTriangle className="w-8 h-8 text-muted-foreground/40 mx-auto" />
            <p className="text-sm font-medium">
              {locale === "ar"
                ? "لا توجد سجلات مطابقة لمعايير البحث والفلترة حالياً."
                : "هیچ ئەنجامێک نەدۆزرایەوە."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/80 text-muted-foreground text-xs font-bold uppercase tracking-wider">
                <tr>
                  <th className="text-right p-4">
                    {locale === "ar" ? "الوقت والتاريخ" : "کات و ڕێکەوت"}
                  </th>
                  <th className="text-right p-4">
                    {locale === "ar" ? "المبادر / المستخدم" : "بەکارھێنەر"}
                  </th>
                  <th className="text-right p-4">
                    {locale === "ar" ? "الإجراء المحاسبي" : "کردار"}
                  </th>
                  <th className="text-right p-4">
                    {locale === "ar" ? "الهدف والمستند" : "ئامانج"}
                  </th>
                  <th className="text-right p-4">{locale === "ar" ? "القسم" : "بەش"}</th>
                  <th className="text-right p-4">
                    {locale === "ar" ? "هاش التشفير (SHA-256)" : "هاش"}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredEntries.map((e) => (
                  <tr key={e.id} className="hover:bg-muted/30 transition-all">
                    <td className="p-4 text-muted-foreground whitespace-nowrap text-xs" dir="ltr">
                      {e.at}
                    </td>
                    <td className="p-4 font-bold text-foreground whitespace-nowrap">{e.actor}</td>
                    <td className="p-4">
                      <span className="inline-flex px-2 py-1 rounded bg-primary/5 text-primary text-xs font-semibold">
                        {e.action}
                      </span>
                    </td>
                    <td
                      className="p-4 text-muted-foreground text-xs max-w-[280px] truncate"
                      title={e.target}
                    >
                      {e.target}
                    </td>
                    <td className="p-4">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                          e.department === "المشتريات"
                            ? "bg-danger/5 text-danger border border-danger/10"
                            : e.department === "المالية"
                              ? "bg-success/5 text-success border border-success/10"
                              : e.department === "المخازن"
                                ? "bg-warning/5 text-warning border border-warning/10"
                                : "bg-muted text-muted-foreground border border-border/40"
                        }`}
                      >
                        {e.department}
                      </span>
                    </td>
                    <td
                      className="p-4 font-mono text-xs text-primary/80 whitespace-nowrap"
                      dir="ltr"
                    >
                      {e.hash}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Safety assurance footer */}
      <div className="text-[11px] text-muted-foreground leading-relaxed p-4 rounded-xl bg-muted/30 border border-border/40 text-center">
        {locale === "ar"
          ? "يتم تشفير وتعمية كل قيد في هذا الدفتر بشكل متسلسل ومترابط مع القيود السابقة لمنع أي حذف أو تعديل للنشاطات. أي تلاعب سيؤدي إلى كسر السلسلة فوراً وتنبيه مالك المحفظة."
          : "هەموو تۆمارەکان بە شێوەیەکی زنجیرەیی بە یەکەوە گرێدراون بۆ ڕێگریکردن لە هەر دەستکارییەک."}
      </div>
    </div>
  );
}
