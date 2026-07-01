import { Link } from "@tanstack/react-router";
import { ChevronLeft, Home } from "lucide-react";
import { useEffect, useState } from "react";
import { getCurrentUser, type AccessibleCompany } from "@/lib/auth";
import { getLocale, type Locale } from "@/lib/i18n";

const LABELS: Record<
  Locale,
  { group: string; company: string; branch: string; portfolio: string; dept: string }
> = {
  ar: { group: "المجموعة", company: "الشركة", branch: "الفرع", portfolio: "محفظة", dept: "القسم" },
  ckb: { group: "گروپ", company: "کۆمپانیا", branch: "لق", portfolio: "پۆرفۆلیۆ", dept: "بەش" },
};

/**
 * Persistent breadcrumb showing the current path: المجموعة ‹ الشركة ‹ الفرع ‹ القسم.
 * Lives in the top bar at every layer.
 */
export function Breadcrumb({ layer }: { layer?: string }) {
  const [user] = useState(() => getCurrentUser());
  const [locale] = useState<Locale>(getLocale());
  const [activeCompany, setActiveCompany] = useState<string | null>(null);
  const [activeBranch, setActiveBranch] = useState<string | null>(null);
  const labels = LABELS[locale];

  useEffect(() => {
    if (typeof window === "undefined") return;
    setActiveCompany(window.localStorage.getItem("auditcore.active.company"));
    setActiveBranch(window.localStorage.getItem("auditcore.active.branch"));
  }, []);

  if (!user) return null;
  const companies = (user.accessibleCompanies || []) as AccessibleCompany[];
  const currentCompany = companies.find((c) => c.company_id === activeCompany) || companies[0];
  const currentBranch = activeBranch
    ? currentCompany?.branches.find((b) => b.branch_id === activeBranch)
    : null;

  return (
    <nav className="flex items-center gap-2 text-xs text-muted-foreground">
      <Link to="/owner" className="hover:text-foreground transition flex items-center gap-1">
        <Home className="w-3 h-3" />
        <span>{labels.portfolio}</span>
      </Link>
      {currentCompany && (
        <>
          <ChevronLeft className="w-3 h-3" />
          <Link
            to="/owner"
            search={{ company: currentCompany.company_id }}
            className="hover:text-foreground transition font-medium"
          >
            <span className="text-muted-foreground/60 me-1">{labels.company} ‹</span>
            {currentCompany.name}
          </Link>
        </>
      )}
      {currentBranch && (
        <>
          <ChevronLeft className="w-3 h-3" />
          <span className="font-medium">
            <span className="text-muted-foreground/60 me-1">{labels.branch} ‹</span>
            {currentBranch.name}
          </span>
        </>
      )}
      {layer && (
        <>
          <ChevronLeft className="w-3 h-3" />
          <span className="text-foreground font-bold">{layer}</span>
        </>
      )}
    </nav>
  );
}
