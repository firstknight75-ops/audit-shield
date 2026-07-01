/**
 * API client — typed, retry-aware, with error envelope parsing.
 *
 * Replaces per-page mock-data usage. Every backend endpoint has a
 * corresponding typed method here. The base URL defaults to /api but
 * can be overridden at runtime via VITE_API_BASE.
 */

export type Locale = "ar" | "ckb";

export type ApiEnvelope<T> = {
  data?: T;
  detail?: string;
  errors?: unknown[];
  request_id?: string;
};

export class ApiError extends Error {
  status: number;
  body: ApiEnvelope<unknown> | null;
  request_id: string | null;
  constructor(status: number, body: ApiEnvelope<unknown> | null, request_id: string | null) {
    super(`api_error_${status}: ${body?.detail ?? "unknown"}`);
    this.status = status;
    this.body = body;
    this.request_id = request_id;
  }
}

type FetchOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  /** Idempotency-Key for write endpoints — backend dedupes within 24h. */
  idempotencyKey?: string;
  /** Disable the default JSON parsing (for raw blob/PDF). */
  raw?: boolean;
};

const DEFAULT_BASE =
  (typeof window !== "undefined"
    ? (window as unknown as { __AUDITCORE_API_BASE__?: string }).__AUDITCORE_API_BASE__
    : undefined) ?? "/api";

let ACCESS_TOKEN: string | null = null;
export function setAccessToken(t: string | null) {
  ACCESS_TOKEN = t;
}

let ACTIVE_COMPANY_ID: string | null = null;
export function setActiveCompanyId(c: string | null) {
  ACTIVE_COMPANY_ID = c;
  if (typeof window !== "undefined") {
    if (c) window.localStorage.setItem("auditcore.active.company", c);
    else window.localStorage.removeItem("auditcore.active.company");
    window.dispatchEvent(new Event("auditcore.active_company_changed"));
  }
}
export function getActiveCompanyId(): string | null {
  if (ACTIVE_COMPANY_ID) return ACTIVE_COMPANY_ID;
  if (typeof window !== "undefined") {
    return window.localStorage.getItem("auditcore.active.company");
  }
  return null;
}

export function isPreviewApiUnavailable(): boolean {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  const usingDefaultApi = DEFAULT_BASE === "/api";
  return (
    usingDefaultApi &&
    (host.includes("lovableproject.com") ||
      host.includes("lovable.app") ||
      host === "localhost" ||
      host === "127.0.0.1")
  );
}

async function request<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const base = DEFAULT_BASE;
  const url = new URL(
    base.replace(/\/$/, "") + (path.startsWith("/") ? path : `/${path}`),
    window.location.origin,
  );
  if (opts.query) {
    for (const [k, v] of Object.entries(opts.query)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Locale":
      (typeof window !== "undefined" &&
        (window.localStorage.getItem("auditcore.locale.v1") as Locale)) ||
      "ar",
    ...opts.headers,
  };
  if (ACCESS_TOKEN) headers.Authorization = `Bearer ${ACCESS_TOKEN}`;
  if (ACTIVE_COMPANY_ID) headers["X-Active-Company"] = ACTIVE_COMPANY_ID;
  if (opts.idempotencyKey) headers["Idempotency-Key"] = opts.idempotencyKey;

  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers,
    credentials: "include",
    signal: opts.signal,
  };
  if (opts.body !== undefined && !opts.raw) {
    init.body = JSON.stringify(opts.body);
    headers["Content-Type"] = "application/json";
  }

  const registerLog = (status: number, detail: string, success: boolean) => {
    if (typeof window !== "undefined") {
      const g = window as any;
      g.__AUDITCORE_API_LOGS__ = g.__AUDITCORE_API_LOGS__ || [];
      g.__AUDITCORE_API_FAILURES__ = g.__AUDITCORE_API_FAILURES__ || 0;
      g.__AUDITCORE_API_SUCCESS__ = g.__AUDITCORE_API_SUCCESS__ || 0;

      g.__AUDITCORE_API_LOGS__.unshift({
        path,
        method: opts.method ?? "GET",
        status,
        timestamp: new Date().toLocaleTimeString(),
        detail,
        success,
      });
      if (success) {
        g.__AUDITCORE_API_SUCCESS__++;
      } else {
        g.__AUDITCORE_API_FAILURES__++;
      }
      if (g.__AUDITCORE_API_LOGS__.length > 50) {
        g.__AUDITCORE_API_LOGS__.pop();
      }
      window.dispatchEvent(new Event("auditcore.api_counters_updated"));
    }
  };

  try {
    const res = await fetch(url.toString(), init);
    const requestId = res.headers.get("x-request-id");

    if (!res.ok) {
      let body: ApiEnvelope<unknown> | null = null;
      try {
        body = (await res.json()) as ApiEnvelope<unknown>;
      } catch {
        /* not JSON */
      }
      const err = new ApiError(res.status, body, requestId);
      registerLog(res.status, body?.detail ?? "HTTP Error Response", false);
      throw err;
    }
    registerLog(res.status, "Success", true);
    if (opts.raw) return (await res.blob()) as unknown as T;
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    const errMsg = err instanceof Error ? err.message : String(err);
    registerLog(0, `Network / Offline connection failure: ${errMsg}`, false);
    throw err;
  }
}

/** Retry-on-5xx with exponential backoff. Idempotent for GETs. */
async function requestWithRetry<T>(
  path: string,
  opts: FetchOptions = {},
  maxRetries = 2,
): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await request<T>(path, opts);
    } catch (e) {
      lastErr = e;
      const isRetryable = e instanceof ApiError && e.status >= 500 && e.status < 600;
      if (!isRetryable || attempt === maxRetries) throw e;
      await new Promise((r) => setTimeout(r, 200 * 2 ** attempt));
    }
  }
  throw lastErr;
}

// ── Endpoints ────────────────────────────────────────────────────

export const api = {
  // ── Auth ──
  auth: {
    login: (email: string, password: string) =>
      requestWithRetry<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        body: { email, password },
      }),
    refresh: (refresh_token: string) =>
      requestWithRetry<{ access_token: string; refresh_token: string }>("/auth/refresh", {
        method: "POST",
        body: { refresh_token },
      }),
    me: () => requestWithRetry<MeResponse>("/auth/me"),
    setLanguage: (preferred_language: Locale) =>
      requestWithRetry<{ preferred_language: Locale }>("/admin/language", {
        method: "POST",
        body: { preferred_language },
      }),
  },

  // ── Owner outputs ──
  owner: {
    picture: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/picture?company_id=${company_id}`),
    trustIndex: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/trust-index?company_id=${company_id}`),
    wasteMap: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/waste-map?company_id=${company_id}`),
    riskMap: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/risk-map?company_id=${company_id}`),
    opportunityMap: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/opportunity-map?company_id=${company_id}`),
    actionPlan: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/action-plan?company_id=${company_id}`),
    portfolio: () => requestWithRetry<unknown>("/owner/portfolio"),
    activation: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/activation?company_id=${company_id}`),
    layer4: (document_id: string, company_id: string) =>
      requestWithRetry<unknown>(
        `/owner/dashboard/layer4/${document_id}/image?company_id=${company_id}`,
        { raw: true },
      ),
    runAnalysis: (company_id: string) =>
      requestWithRetry<unknown>(`/analytics/run/${company_id}`, { method: "POST" }),
    verifyLedger: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/ledger/verify?company_id=${company_id}`),
    aiAdvisor: (company_id: string) =>
      requestWithRetry<unknown>(`/owner/ai-advisor?company_id=${company_id}`),
  },

  // ── Auditor ──
  auditor: {
    next: (company_id: string) =>
      requestWithRetry<unknown>(`/certification/next?company_id=${company_id}`),
    certify: (
      extraction_id: string,
      payload: { fields: Record<string, unknown> },
      company_id: string,
    ) =>
      requestWithRetry<unknown>(
        `/certification/${extraction_id}/certify?company_id=${company_id}`,
        {
          method: "POST",
          body: payload,
        },
      ),
    upload: (formData: FormData) =>
      requestWithRetry<unknown>("/documents/upload", { method: "POST", body: formData }),
  },

  // ── Manager ──
  manager: {
    dashboard: (company_id: string, branch_id?: string) =>
      requestWithRetry<unknown>(
        `/analytics/manager/dashboard?company_id=${company_id}${branch_id ? `&branch_id=${branch_id}` : ""}`,
      ),
    widgets: (company_id: string, branch_id?: string) =>
      requestWithRetry<unknown>(
        `/manager/widgets?company_id=${company_id}${branch_id ? `&branch_id=${branch_id}` : ""}`,
      ),
  },

  // ── Exports ──
  exports: {
    run: (company_id: string, output_code: string, format: "excel" | "pdf" | "png") =>
      requestWithRetry<unknown>(`/exports/run?company_id=${company_id}`, {
        method: "POST",
        body: { output_code, format },
      }),
    whatIf: (company_id: string, payload: unknown) =>
      requestWithRetry<unknown>(`/what-if/run?company_id=${company_id}`, {
        method: "POST",
        body: payload,
      }),
  },

  // ── Trust Center (live data) ──
  trust: {
    proofs: () => requestWithRetry<unknown>("/trust-proof/run"),
  },

  // ── Trust verification (public, no login) ──
  verify: {
    public: (
      report_id: string,
      payload: {
        ledger_hash_at_generation: string;
        signature: string;
        payload: Record<string, unknown>;
      },
    ) => requestWithRetry<unknown>(`/verify/${report_id}`, { method: "POST", body: payload }),
  },

  // ── Notifications inbox ──
  inapp: {
    unreadCount: () => requestWithRetry<{ count: number }>("/inapp/unread"),
    recent: (limit = 50) => requestWithRetry<unknown[]>(`/inapp/recent?limit=${limit}`),
    markRead: (id: string) =>
      requestWithRetry<{ ok: boolean }>(`/inapp/${id}/read`, { method: "POST" }),
    markAllRead: () => requestWithRetry<{ ok: boolean }>("/inapp/read-all", { method: "POST" }),
  },

  // ── Search ──
  search: {
    documents: (q: string, opts?: { company_id?: string; limit?: number }) => {
      const query: Record<string, string> = { q };
      if (opts?.company_id) query.company_id = opts.company_id;
      if (opts?.limit) query.limit = String(opts.limit);
      return requestWithRetry<unknown[]>("/search/documents", { query });
    },
  },

  // ── AI feedback ──
  ai: {
    feedback: (
      finding_id: string,
      finding_kind: string,
      rating: "correct" | "false_positive" | "missed",
      note?: string,
    ) =>
      requestWithRetry<unknown>("/ai/feedback", {
        method: "POST",
        body: { finding_id, finding_kind, rating, note },
      }),
  },

  // ── System ──
  system: {
    featureFlags: () => requestWithRetry<Record<string, unknown>>("/system/feature-flags"),
  },
};

// ── Types ────────────────────────────────────────────────────────

export type MeResponse = {
  id: string;
  email: string;
  full_name: string;
  role: "owner" | "gm" | "manager" | "auditor" | "admin" | "appowner";
  preferred_language: Locale;
  permissions: string[];
  accessible_companies: Array<{
    company_id: string;
    name: string;
    branches: Array<{ branch_id: string; name: string }>;
  }>;
  last_activity_at: string | null;
};
