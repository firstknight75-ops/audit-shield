import arAuth from '@/locales/ar/auth.json';
import ckbAuth from '@/locales/ckb/auth.json';
import arDashboard from '@/locales/ar/dashboard.json';
import ckbDashboard from '@/locales/ckb/dashboard.json';
import arCertification from '@/locales/ar/certification.json';
import ckbCertification from '@/locales/ckb/certification.json';
import arAdmin from '@/locales/ar/admin.json';
import ckbAdmin from '@/locales/ckb/admin.json';

export type Locale = 'ar' | 'ckb';

export const bundles = {
  ar: { auth: arAuth, dashboard: arDashboard, certification: arCertification, admin: arAdmin },
  ckb: { auth: ckbAuth, dashboard: ckbDashboard, certification: ckbCertification, admin: ckbAdmin },
};

export type Namespace = keyof typeof bundles.ar;

const KEY = 'auditcore.locale.v1';

export function getLocale(): Locale {
  if (typeof window === 'undefined') return 'ar';
  return (window.localStorage.getItem(KEY) as Locale) || 'ar';
}

export function setLocale(locale: Locale) {
  if (typeof window !== 'undefined') window.localStorage.setItem(KEY, locale);
}

export function t(ns: Namespace, key: string, locale: Locale): string {
  return (bundles[locale][ns] as Record<string, string>)[key] || key;
}

/** Get all keys for a namespace (useful for build-time completeness checks). */
export function getNamespaceKeys(ns: Namespace): string[] {
  return Object.keys(bundles.ar[ns]);
}
