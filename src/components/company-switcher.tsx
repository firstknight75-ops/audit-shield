import { useEffect, useState } from "react";
import { Building2, ChevronDown, GitBranch } from "lucide-react";
import { getCurrentUser, type AccessibleCompany } from "@/lib/auth";
import { getLocale, type Locale } from "@/lib/i18n";
import { getActiveCompanyId, setActiveCompanyId } from "@/lib/api-client";

const LABELS: Record<Locale, { group: string; company: string; branch: string; allBranches: string; pickCompany: string }> = {
  ar: { group: "المجموعة", company: "الشركة", branch: "الفرع", allBranches: "كل الفروع", pickCompany: "اختر شركة" },
  ckb: { group: "گروپ", company: "کۆمپانیا", branch: "لق", allBranches: "هەموو لقەکان", pickCompany: "کۆمپانیایەک هەڵبژێرە" },
};

/**
 * CompanySwitcher — the persistent company/branch switcher that lives in
 * the top bar at every layer. The Owner moves sideways without retracing
 * to the portfolio view. Auto-skips itself if the user has access to
 * exactly one company AND one branch.
 */
export function CompanySwitcher() {
  const [user] = useState(() => getCurrentUser());
  const [locale] = useState<Locale>(getLocale());
  const [activeCompany, setActiveCompany] = useState<string | null>(null);
  const [activeBranch, setActiveBranch] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const labels = LABELS[locale];

  useEffect(() => {
    if (typeof window === "undefined") return;
    const cid = getActiveCompanyId();
    const bid = window.localStorage.getItem("auditcore.active.branch");
    setActiveCompany(cid);
    setActiveBranch(bid);
    const onCompanyChanged = () => {
      setActiveCompany(getActiveCompanyId());
      setActiveBranch(window.localStorage.getItem("auditcore.active.branch"));
    };
    window.addEventListener("auditcore.active_company_changed", onCompanyChanged);
    return () => window.removeEventListener("auditcore.active_company_changed", onCompanyChanged);
  }, []);

  if (!user || !user.accessibleCompanies) return null;
  const companies = user.accessibleCompanies as AccessibleCompany[];
  if (companies.length === 0) return null;
  // Auto-skip if exactly one company AND only branches <=1
  const totalBranches = companies.reduce((s, c) => s + c.branches.length, 0);
  if (companies.length === 1 && totalBranches <= 1) return null;

  const currentCompany = companies.find((c) => c.company_id === activeCompany) || companies[0];
  const branches = currentCompany.branches;

  const selectCompany = (cid: string) => {
    setActiveCompany(cid);
    setActiveBranch(null);
    if (typeof window !== "undefined") {
      setActiveCompanyId(cid);
      window.localStorage.removeItem("auditcore.active.branch");
    }
    setOpen(false);
  };
  const selectBranch = (bid: string | null) => {
    setActiveBranch(bid);
    if (typeof window !== "undefined") {
      if (bid) window.localStorage.setItem("auditcore.active.branch", bid);
      else window.localStorage.removeItem("auditcore.active.branch");
      window.dispatchEvent(new Event("auditcore.active_company_changed"));
    }
    setOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border bg-card hover:border-primary transition text-sm"
      >
        <Building2 className="w-4 h-4 text-primary" />
        <span className="font-medium">{currentCompany.name}</span>
        {activeBranch && currentCompany.branches.find((b) => b.branch_id === activeBranch) && (
          <>
            <span className="text-muted-foreground">/</span>
            <GitBranch className="w-3 h-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              {currentCompany.branches.find((b) => b.branch_id === activeBranch)?.name}
            </span>
          </>
        )}
        <ChevronDown className="w-3 h-3 text-muted-foreground" />
      </button>
      {open && (
        <div className="absolute end-0 mt-2 w-72 bg-popover border border-border rounded-xl shadow-2xl z-50 p-2">
          <div className="px-2 py-1 text-[10px] uppercase tracking-wide text-muted-foreground">{labels.pickCompany}</div>
          <div className="space-y-1">
            {companies.map((c) => (
              <div key={c.company_id}>
                <button
                  onClick={() => selectCompany(c.company_id)}
                  className={`w-full text-start px-3 py-2 rounded-md text-sm hover:bg-sidebar-accent transition flex items-center gap-2 ${c.company_id === currentCompany.company_id ? "bg-primary/10 text-primary" : ""}`}
                >
                  <Building2 className="w-3 h-3" />
                  <span className="flex-1">{c.name}</span>
                  <span className="text-[10px] text-muted-foreground">{labels.company}</span>
                </button>
                {c.company_id === currentCompany.company_id && c.branches.length > 0 && (
                  <div className="ms-4 mt-1 space-y-1 border-s border-border ps-2">
                    <button
                      onClick={() => selectBranch(null)}
                      className={`w-full text-start px-2 py-1.5 rounded text-xs hover:bg-sidebar-accent transition flex items-center gap-1 ${!activeBranch ? "bg-primary/10 text-primary" : "text-muted-foreground"}`}
                    >
                      <GitBranch className="w-3 h-3" /> {labels.allBranches}
                    </button>
                    {c.branches.map((b) => (
                      <button
                        key={b.branch_id}
                        onClick={() => selectBranch(b.branch_id)}
                        className={`w-full text-start px-2 py-1.5 rounded text-xs hover:bg-sidebar-accent transition flex items-center gap-1 ${activeBranch === b.branch_id ? "bg-primary/10 text-primary" : "text-muted-foreground"}`}
                      >
                        <GitBranch className="w-3 h-3" /> {b.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
