import { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Loading skeleton — shaped like the real content. Replaces generic spinners.
 * Per Phase 3 spec: "loading states are skeletons shaped like the real content,
 * not generic spinners".
 */

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%]",
        className,
      )}
      aria-busy="true"
      aria-live="polite"
    />
  );
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={cn("h-3", i === lines - 1 ? "w-2/3" : "w-full")} />
      ))}
    </div>
  );
}

export function SkeletonCard({ className, children }: SkeletonProps & { children?: ReactNode }) {
  return (
    <div className={cn("p-6 rounded-xl bg-card border border-border", className)}>
      {children ?? <SkeletonText lines={3} />}
    </div>
  );
}

/**
 * KPI-card skeleton — exactly 5 cards, matching the Executive layer layout.
 */
export function ExecutiveSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="p-5 rounded-2xl bg-card border border-border">
          <Skeleton className="h-9 w-9 rounded-lg mb-4" />
          <Skeleton className="h-3 w-3/4 mb-3" />
          <Skeleton className="h-6 w-1/2" />
        </div>
      ))}
    </div>
  );
}

/**
 * Inline "جاري تحليل البيانات..." message — appears at the actual point
 * of waiting, in both Arabic and Sorani based on locale.
 */
export function AnalyzingMessage({ locale }: { locale: "ar" | "ckb" }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground italic">
      <span className="inline-block w-2 h-2 rounded-full bg-primary animate-pulse" />
      <span>{locale === "ar" ? "جاري تحليل البيانات..." : "لە شیکردنەوەی داتاکاندا..."}</span>
    </div>
  );
}
