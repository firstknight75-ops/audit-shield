// Mock analytics — these would come from RLS-protected tables in prod.
// All amounts in IQD.

export const ownerKpis = {
  monthlyWaste: 184_500_000,
  trustIndex: 78,
  criticalAlerts: 7,
  predictedCash: 612_000_000,
  auditorEfficiency: 91,
  chainIntegrity: 100,
};

export const wasteByDepartment = [
  { name: "المشتريات", value: 78_200_000 },
  { name: "المخازن", value: 42_300_000 },
  { name: "المبيعات", value: 28_900_000 },
  { name: "الموارد البشرية", value: 19_100_000 },
  { name: "الإنتاج", value: 16_000_000 },
];

export const wasteByCategory = [
  { name: "هدر مالي", value: 88_000_000 },
  { name: "هدر تشغيلي", value: 46_000_000 },
  { name: "هدر بشري", value: 31_000_000 },
  { name: "فرص ضائعة", value: 19_500_000 },
];

export const cashTrend = [
  { month: "تموز", in: 480, out: 420 },
  { month: "آب", in: 510, out: 445 },
  { month: "أيلول", in: 495, out: 460 },
  { month: "تشرين 1", in: 530, out: 471 },
  { month: "تشرين 2", in: 555, out: 498 },
  { month: "كانون 1", in: 612, out: 520 },
];

export const riskAlerts = [
  { id: "r1", severity: "critical", title: "فاتورة مكررة بمبلغ 12,400,000 د.ع", department: "المشتريات", impact: 12_400_000 },
  { id: "r2", severity: "critical", title: "تباين بين الشراء والمخزن — 8 أصناف", department: "المخازن", impact: 6_800_000 },
  { id: "r3", severity: "high", title: "صرف نقدي بدون مستند مساند", department: "المالية", impact: 3_200_000 },
  { id: "r4", severity: "high", title: "تأخر تسوية حساب بنكي 14 يوم", department: "المالية", impact: 0 },
  { id: "r5", severity: "medium", title: "زيادة شاذة في مصاريف الوقود", department: "النقل", impact: 1_900_000 },
];

export const pendingDocuments = [
  { id: "d1", filename: "INV-2026-0481.pdf", category: "فاتورة شراء", confidence: 92, status: "pending" },
  { id: "d2", filename: "كشف-حساب-بنكي-حزيران.pdf", category: "كشف حساب بنكي", confidence: 71, status: "pending" },
  { id: "d3", filename: "عقد-مورد-جديد.docx", category: "عقد", confidence: 55, status: "pending" },
  { id: "d4", filename: "تقرير-جرد-المخزن.xlsx", category: "تقرير جرد", confidence: 88, status: "pending" },
];

export const sampleInvoice = {
  id: "d1",
  filename: "INV-2026-0481.pdf",
  imageUrl: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=900&q=80",
  fields: [
    { key: "invoice_number", label: "رقم الفاتورة", value: "INV-2026-0481", confidence: 96 },
    { key: "date", label: "التاريخ", value: "2026-06-12", confidence: 91 },
    { key: "vendor", label: "اسم المورد", value: "شركة الرافدين للتجارة", confidence: 84 },
    { key: "amount", label: "المبلغ الإجمالي (د.ع)", value: "12,450,000", confidence: 58 },
    { key: "tax", label: "الضريبة", value: "", confidence: 0 },
  ],
};

export const auditorTasks = [
  { id: "t1", title: "اعتماد فاتورة INV-2026-0481", type: "OCR", sla: "خلال ساعتين", status: "open", remaining: 88, demerits: 0 },
  { id: "t2", title: "مطابقة كشف حساب بنكي - حزيران", type: "كشف بنكي", sla: "اليوم", status: "open", remaining: 380, demerits: 0 },
  { id: "t3", title: "مراجعة قيد عكسي #4421", type: "قيد عكسي", sla: "متأخر", status: "overdue", remaining: -20, demerits: 3 },
  { id: "t4", title: "اعتماد تقرير جرد المخزن", type: "OCR", sla: "خلال 4 ساعات", status: "open", remaining: 210, demerits: 0 },
];

export const ledgerEntries = [
  { id: "l1", at: "2026-06-28 09:14", actor: "زينب الكاظمي", action: "اعتماد مستند", target: "INV-2026-0481", hash: "a7c3…91f" },
  { id: "l2", at: "2026-06-28 09:02", actor: "زينب الكاظمي", action: "تصحيح OCR", target: "حقل المبلغ: 12,400,000 → 12,450,000", hash: "b21d…44a" },
  { id: "l3", at: "2026-06-28 08:31", actor: "مصطفى", action: "منح صلاحية مؤقتة", target: "view_waste_map → مدير المشتريات (7 أيام)", hash: "9e88…0c2" },
  { id: "l4", at: "2026-06-28 02:00", actor: "النظام", action: "تشغيل التحليل اليومي", target: "Trust Index = 78", hash: "5ff1…7b9" },
];

export const clients = [
  { id: "c1", name: "مجموعة النخيل التجارية", sector: "تجارة", tier: "elite", users: 24, cap: 50, lastBackup: "قبل 6 ساعات", health: "ok" },
  { id: "c2", name: "مصنع الفرات للأغذية", sector: "تصنيع", tier: "advanced", users: 12, cap: 20, lastBackup: "قبل 8 ساعات", health: "ok" },
  { id: "c3", name: "مطاعم بغداد العريقة", sector: "مطاعم", tier: "essential", users: 6, cap: 10, lastBackup: "قبل يومين", health: "warning" },
  { id: "c4", name: "العقارية المتحدة", sector: "عقارات", tier: "advanced", users: 9, cap: 20, lastBackup: "قبل 3 ساعات", health: "ok" },
];

export const formatIQD = (n: number) =>
  new Intl.NumberFormat("ar-IQ").format(n) + " د.ع";

export const ownerLayer2 = [
  { department: "المشتريات", score: 5, amount: 12400000 },
  { department: "المخازن", score: 4, amount: 6800000 },
  { department: "المالية", score: 3, amount: 3200000 },
];

export const ownerLayer3 = [
  { id: "f1", type: "duplicate_invoice", title: "فاتورة مكررة", invoice: "INV-2026-9001", amount: 12400000 },
  { id: "f2", type: "procurement_inventory_mismatch", title: "تضارب مشتريات/مخزن", invoice: "INV-2026-9002", amount: 6800000 },
];

export const ownerLayer4 = {
  documentId: "d1",
  filename: "arabic-invoice.jpg",
  imageUrl: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=900&q=80",
  ledger: [
    { id: "l1", action: "document_uploaded", at: "2026-06-28 08:10" },
    { id: "l2", action: "ocr_processed", at: "2026-06-28 08:11" },
    { id: "l3", action: "document_certified", at: "2026-06-28 08:14" },
    { id: "l4", action: "daily_analysis_completed", at: "2026-06-28 02:00" },
  ],
};
