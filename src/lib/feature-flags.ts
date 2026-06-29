/**
 * Feature Flags — runtime toggleable flags for safe rollouts + A/B tests.
 *
 * Two layers:
 * - Static defaults (compile-time)
 * - Backend overrides (fetched from /api/system/feature-flags at startup;
 *   overrides stored in Redis with 60s TTL)
 *
 * Usage:
 *   if (await featureFlags.isEnabled('new_dashboard_v2', user)) {
 *     return <NewDashboard />;
 *   }
 *
 * Server-side evaluation: tenant/role/user overrides are checked via
 * `evaluateFlag` against the user's `role` and `company_group_id`.
 */

import { api, getActiveCompanyId } from "@/lib/api-client";

type FlagContext = {
  user_id?: string;
  role?: "owner" | "gm" | "manager" | "auditor" | "admin" | "appowner";
  company_id?: string;
};

export type Flag = {
  key: string;
  enabled: boolean;
  description?: string;
  rollout_percentage?: number;
  allow_roles?: string[];
  allow_company_ids?: string[];
  expires_at?: string;
};

// Static defaults — overridden by /api/system/feature-flags at startup.
const DEFAULTS: Record<string, Flag> = {
  // Safe rollout flags
  'trust_center.public': {
    key: 'trust_center.public',
    enabled: true,
    description: 'Public Trust Center at /trust (no login)',
  },
  'audit.dual_language_required': {
    key: 'audit.dual_language_required',
    enabled: true,
    description: 'Every Arabic string must have a Sorani counterpart before shipping',
  },
  'reporting.watermarks_enabled': {
    key: 'reporting.watermarks_enabled',
    enabled: true,
  },
  'activation.banner_48h_enabled': {
    key: 'activation.banner_48h_enabled',
    enabled: true,
  },
  'inapp.notifications.enabled': {
    key: 'inapp.notifications.enabled',
    enabled: true,
  },
  'workflow.sla_breach_alerts': {
    key: 'workflow.sla_breach_alerts',
    enabled: true,
  },
  // Disabled by default — gated behind explicit enable
  'ai.feedback_loop_active': {
    key: 'ai.feedback_loop_active',
    enabled: false,
    description: 'Enable AI feedback retraining (off until models are calibrated)',
  },
  'ocr.gpu_acceleration': {
    key: 'ocr.gpu_acceleration',
    enabled: false,
    description: 'GPU-accelerated Tesseract (requires CUDA tesseract build)',
  },
};

class FeatureFlagRegistry {
  private overrides: Map<string, Flag> = new Map();
  private lastFetchedAt: number | null = null;
  private static REFRESH_MS = 60_000;

  /** Evaluate a flag against a context (user/role/company). */
  evaluate(key: string, ctx: FlagContext = {}): boolean {
    const flag = this.overrides.get(key) ?? DEFAULTS[key];
    if (!flag) return false;
    if (!flag.enabled) return false;
    if (flag.expires_at && new Date(flag.expires_at) < new Date()) return false;
    if (flag.allow_roles?.length && ctx.role && !flag.allow_roles.includes(ctx.role)) return false;
    if (flag.allow_company_ids?.length && ctx.company_id && !flag.allow_company_ids.includes(ctx.company_id)) return false;
    if (flag.rollout_percentage !== undefined && ctx.user_id) {
      // Deterministic hash-based rollout
      const hash = Array.from(ctx.user_id).reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) >>> 0, 0);
      const bucket = hash % 100;
      if (bucket >= flag.rollout_percentage) return false;
    }
    return true;
  }

  /** Fetch fresh overrides from the backend. */
  async refresh(): Promise<void> {
    try {
      const res = await api.system.featureFlags();
      this.overrides = new Map(Object.entries((res || {}) as Record<string, Flag>));
      this.lastFetchedAt = Date.now();
    } catch {
      // Tolerate — fall back to defaults
    }
  }

  isStale(): boolean {
    return this.lastFetchedAt === null || Date.now() - this.lastFetchedAt > FeatureFlagRegistry.REFRESH_MS;
  }
}

export const featureFlags = new FeatureFlagRegistry();

// Convenience helpers
export const flags = {
  isEnabled: (key: string, ctx: FlagContext = {}) => featureFlags.evaluate(key, ctx),
  refresh: () => featureFlags.refresh(),
};

// Auto-refresh every minute
if (typeof window !== "undefined") {
  setInterval(() => {
    if (featureFlags.isStale()) featureFlags.refresh();
  }, 60_000);
}
