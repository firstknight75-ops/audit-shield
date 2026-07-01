# AuditCore / Audit Shield - Ultimate System Blueprint & Architecture

This document serves as the absolute and final **System Blueprint** for **AuditCore**, detailing the fully updated system concept, core rules, the six dimensions, technical features/services, and a complete inventory of all role-based screens.

---

## 1. Core Concept & Philosophy (فلسفة المفهوم الجديد)

The central value proposition of **AuditCore** has successfully pivoted from "audit automation" to **"Auditing the Auditor & Report Translation for Non-Specialists" (تدقيق المدقق وتفسير التقارير لغير المتخصصين)**.

### The Core Pain Point:

A business owner owning 12 different companies or branches has **neither the time nor the technical accounting background** to sift through thousands of spreadsheet rows, complex ledger logs, or dry audit reports. They need to know exactly:

1.  **"What does this number actually mean?" (شنو يعني هذا الرقم فعلياً؟)**
2.  **"Where is the hidden risk or fraud?" (وين الخطر؟)**
3.  **"What action should I take right now?" (شنو أسوي الحين؟)**

### The Architectural Solution:

AuditCore operates on **two parallel auditing layers** that intersect at a central component called the **"Smart Bridge" (الجسر الذكي)**:

- **Layer 1 (Internal Audit):** Active, declared auditing across six operational dimensions of the company.
- **Layer 2 (Silent External Audit - التدقيق الصامت):** Back-end, silent reconciliation of routine department reports without their direct knowledge (preventing the _Hawthorne effect_).
- **The Smart Bridge (الجسر الذكي):** Automatically reconciles Layer 1 (official declarations) against Layer 2 (raw file data). Any discrepancy is flagged immediately as a **Critical Deviation / Potential Manipulation**.

---

## 2. The 5 Non-Negotiable Core Rules (القواعد الخمس الأساسية)

Every feature, service, and database schema in AuditCore is built upon five foundational constraints:

1.  **Immutable Ledger (ثبات الإدخال):** No `UPDATE` or `DELETE` operations are ever permitted on the financial ledger (`audit_ledger`). Corrections can only be made via documented **Reversing Entries (قيود عكسية)** referencing the original, retaining absolute tamper-proof audit trails.
2.  **Trust Index (مؤشر الموثوقية):** Every data-entry error, missing field, or duplicate invoice is logged, weighted by severity, and computed into a deterministic **0-100 Trust Score** displayed as a first-class executive KPI.
3.  **File-Only Input (الإدخال عبر الملفات):** No manual ledger insertions are allowed. All data enters via document upload (Excel, CSV, PDF, PNG invoice). The system runs local OCR/AI extraction, displaying the results to an authorized human auditor for manual verification before committing.
4.  **Manipulation Detection (كشف التلاعب):** The engine continuously scans for four key patterns: cross-department contradictions, abnormal spend patterns, duplicate hashes, and logical input/output gaps.
5.  **Customization Configuration Profiles (التخصيص القطاعي):** Each company (tenant) has a custom configuration profile defining its sector-type (Retail, Manufacturing, contracting) and tailored anomaly thresholds.

---

## 3. The 6 Core Audit Dimensions & Detailed KPIs (الأبعاد الستة للتدقيق)

AuditCore acts as six independent engines that share a unified visualization layer:

### 1. Financial Audit (التدقيق المالي)

- _Sources:_ Financial statements, bank statements, invoices, cash logs, AR/AP.
- _KPIs:_ Liquidity, profitability, cash flow velocity, collectability cycle.

### 2. Operational Audit (التدقيق التشغيلي)

- _Sources:_ Production reports, maintenance logs, waste rates, delivery times.
- _KPIs:_ Production efficiency, SLA compliance, sector-specific waste margins.

### 3. Administrative Audit (التدقيق الإداري)

- _Sources:_ Org charts, meeting minutes, HR rosters, attendance records.
- _Administrative KPIs (تُحسب كمياً بالكامل):_
  - **Employee Turnover (معدل الدوران):** Alert on localized department spikes.
  - **Revenue per Employee (إنتاجية الموظف):** Scans for redundant staff or falling efficiency.
  - **Cycle Time (وقت تنفيذ الطلب):** Average time between customer order and full delivery.

### 4. Commercial Audit (التدقيق التجاري)

- _Sources:_ Sales logs, customer transaction history, isolated marketing spend.
- _Commercial KPIs (تُحسب كمياً بالكامل):_
  - **Customer Acquisition Cost (CAC):** Marketing spend ÷ new customers.
  - **Customer Lifetime Value (LTV):** Purchase value × frequency × duration.
  - **LTV:CAC Ratio:** Alert if under the healthy 3:1 threshold.
  - **Customer Retention Rate:** Early-warning churn index.
  - **Concentration Risk (تركز العملاء):** Alerts if a single client represents >30% of revenue.

### 5. Human Performance Audit (تدقيق الأداء البشري)

- _Sources:_ Employee evaluations, localized attendance, individual output metrics.
- _KPIs:_ Individual variance from target, unauthorized absenteeism.
- _Privacy:_ Strictly restricted to Owner and authorized HR managers.

### 6. Compliance Audit (تدقيق الامتثال)

- _Sources:_ Licenses, tax returns, Central Bank of Iraq (CBI) regulations, labor contracts.
- _KPIs:_ License expiration dates, regulatory compliance gaps.

---

## 4. Key Services & Features Built & Wired (الخدمات البرمجية المطورة)

We have successfully engineered and wired the following production-grade services:

- **Active Company Session Persistence (`api-client.ts` & `company-switcher.tsx`):**
  Implements a custom window event `auditcore.active_company_changed` dispatched when the company switcher changes. All open pages (Advisor, Trust Index, Home) listen and re-fetch instantly, storing the selection in `localStorage` for permanent reload persistence.
- **Discreet API Call Failure Monitor Widget (`app-shell.tsx`):**
  Intercepts and logs every request, method, status code, and latency in a global log array. Displays a compact, sleek bottom-left floating widget (`🟢 متصل (12/0)`) that expands on-click into an overlay terminal for quick troubleshooting without cluttering the premium owner experience.
- **Strict PostgreSQL RLS Enforcement (`owner_outputs.py`):**
  Manually overrides and hard-sets connection session context variables (`app.current_user_role` and `app.current_tenant_id`) within the SQLAlchemy transaction scope for every owner query, guaranteeing total tenant data isolation at the DB level.
- **Unified Offline Mock Fallbacks (`owner.advisor.tsx` & `owner.trust-index.tsx`):**
  When running in decoupled frontend-only sandboxes (like Lovable's preview) where the FastAPI server is unreachable, the API calls fail gracefully. The custom hooks intercept the error, display a clear, techy loading status message, and fallback to high-fidelity mock data.
- **PDF Exporter with UTC Date & Tamper-Proof Signature (`engine.py` & `phase4.py`):**
  Expanded the WeasyPrint/HTML PDF exporter to support `ai_advisor` reports. Automatically generates a clean, bilingual RTL PDF embedded with a **Tamper-Proof Certificate** (HMAC-SHA256 signature, `report_id`, and `ledger_hash_at_generation`) and the exact generation date in UTC.

---

## 5. Complete Inventory of All Screens (جرد كامل لكافة الشاشات)

AuditCore is built with clear role-based visualization tiers.

### 1. Owner Tiers (لوحات المالك الاستشارية - 12 شركة)

- **Executive Dashboard (`/owner/index`):**
  - _Features:_ Horizontal tabs for switching between the 12 companies, unified KPI summary cards with trend sparklines (Waste, Trust Index, Critical Alerts, Predicted Cash, Auditor Efficiency), clickable strategic narrative card, and direct recommendations lists.
- **Automated AI Advisor (`/owner/advisor`):**
  - _Features:_ The flagship view. Displays the translated plain-language "Strategic Summary," an interactive chatbot with preset owner-centric questions, an interactive technical-to-business translator, and real-time demerit scores auditing the auditor.
- **Trust Index Hub (`/owner/trust-index`):**
  - _Features:_ Circular SVG progress ring indicating the deterministic 0-100 data quality score, 4 detailed component tiles (Coverage, Certified, Missing Fields, Duplicates), and a 6-cycle bar-chart trend graph.
- **Waste Map Viewer (`/owner/waste-map`):**
  - _Features:_ List of leaks categorized by department, showing the exact financial impact translated into Iraqi Dinars (IQD) and a direct link to view the original uploaded invoice.
- **Risk Map (`/owner/risk-map`):**
  - _Features:_ Traffic-light severity cards (Critical, High, Medium) displaying logical contradictions discovered between different departments.
- **Decision Simulator (`/owner/what-if`):**
  - _Features:_ Slider controls allowing the owner to simulate the financial recovery of a leak over a 6-month horizon, with a PDF export button.
- **Secure Activity Ledger (`/owner/ledger`):**
  - _Features:_ Fully searchable append-only transaction log. Contains department filter tabs, period filters, sort-by-date toggles (newest updates first), SHA-256 hashes, and a "Verify Chain Integrity" trigger.

### 2. Auditor Tiers (لوحات شاشات المدققين)

- **Certification Environment (`/auditor`):**
  - _Features:_ Splitscreen layout showing the original scanned document/invoice on the left and the AI-extracted fields with color-coded confidence levels on the right. Auditors must certify or correct fields before committing.
- **My Daily Tasks (`/auditor/tasks`):**
  - _Features:_ Queue of assigned certification items with strict countdown timers indicating remaining SLA minutes before demerit points are deducted.
- **Upload Document (`/auditor/upload`):**
  - _Features:_ Secure drag-and-drop file upload area supporting CSV, XLSX, PDF, PNG, and JPG.

### 3. Manager Tiers (لوحات مدراء الأقسام الفردية)

- **Department Dashboard (`/manager`):**
  - _Features:_ Draggable and customizable widget layout scoped strictly to their company/branch, displaying budget status, team performance, and quality indices.
- **Correction Tasks (`/manager/tasks`):**
  - _Features:_ Actionable lists of deviations requiring the manager's review, where corrections are submitted as reversal justify comments.

### 4. App Owner Tiers (لوحات صيانة المنصة والشركة المستضيفة)

- **Client Management Console (`/appowner`):**
  - _Features:_ Client listing, backup indicators, subscription tiers management (Essential, Advanced, Elite), and "pooled-to-elite" dedicated database migration triggers.
- **Template Editor (`/appowner/templates`):**
  - _Features:_ No-code preset editor to compile and push permission templates to clients via VPN or CI/CD pipelines, with complete version rollback controls.
- **Maintenance & Operations Logs (`/appowner/maintenance`):**
  - _Features:_ System logs, cross-tenant health polling, container down events, and alert triggers.
