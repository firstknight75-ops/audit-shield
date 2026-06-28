import arAuth from '@/locales/ar/auth.json';
import ckbAuth from '@/locales/ckb/auth.json';
import arDashboard from '@/locales/ar/dashboard.json';
import ckbDashboard from '@/locales/ckb/dashboard.json';

export type Locale = 'ar' | 'ckb';

export const bundles = {
  ar: { auth: arAuth, dashboard: arDashboard },
  ckb: { auth: ckbAuth, dashboard: ckbDashboard },
};

const KEY = 'auditcore.locale.v1';

export function getLocale(): Locale {
  if (typeof window === 'undefined') return 'ar';
  return (window.localStorage.getItem(KEY) as Locale) || 'ar';
}

export function setLocale(locale: Locale) {
  if (typeof window !== 'undefined') window.localStorage.setItem(KEY, locale);
}

export function t(ns: keyof typeof bundles.ar, key: string, locale: Locale) {
  return (bundles[locale][ns] as Record<string, string>)[key] || key;
}
