/**
 * Accessibility helpers — WCAG 2.2 AA compliance.
 *
 * Provides:
 * - useFocusTrap — for modals/dialogs
 * - useReducedMotion — respect prefers-reduced-motion
 * - useRovingTabIndex — keyboard navigation for grids/menus
 * - useLiveRegion — announce async changes to screen readers
 * - aria helpers
 */

import { useEffect, useRef, useState, useCallback } from "react";

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * useLiveRegion — push messages into an aria-live region for screen readers.
 * Returns [announce(message), liveRegionProps].
 */
export function useLiveRegion(politeness: "polite" | "assertive" = "polite") {
  const [msg, setMsg] = useState<string>("");
  const announce = useCallback((m: string) => {
    // Clear first so the same message re-announces
    setMsg("");
    setTimeout(() => setMsg(m), 50);
  }, []);
  return {
    announce,
    liveRegionProps: {
      "aria-live": politeness,
      "aria-atomic": true,
      role: "status",
    },
    message: msg,
  };
}

/**
 * useFocusTrap — when active, focus is kept within `containerRef`.
 * Tab and Shift+Tab cycle through focusable elements.
 * Use for modals, dialogs, dropdowns.
 */
export function useFocusTrap(active: boolean) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!active || !containerRef.current) return;
    const root = containerRef.current;
    const sel =
      'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';
    const focusables = Array.from(root.querySelectorAll<HTMLElement>(sel));
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    first.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    root.addEventListener("keydown", onKey);
    return () => root.removeEventListener("keydown", onKey);
  }, [active]);
  return containerRef;
}

/**
 * useRovingTabIndex — implements ARIA "tab" pattern keyboard nav.
 */
export function useRovingTabIndex(itemCount: number) {
  const [active, setActive] = useState(0);
  const onKey = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        e.preventDefault();
        setActive((i) => (i + 1) % itemCount);
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        e.preventDefault();
        setActive((i) => (i - 1 + itemCount) % itemCount);
      } else if (e.key === "Home") {
        e.preventDefault();
        setActive(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setActive(itemCount - 1);
      }
    },
    [itemCount],
  );
  const tabIndex = useCallback((i: number) => (i === active ? 0 : -1), [active]);
  return { active, setActive, onKey, tabIndex };
}

/**
 * Helper to compose accessible button labels in both languages.
 */
export function accessibleLabel(action: string, target?: string) {
  if (target) return `${action}: ${target}`;
  return action;
}
