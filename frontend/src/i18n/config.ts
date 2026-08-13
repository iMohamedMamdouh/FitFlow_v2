/**
 * اللغة والاتجاه والمظهر — تعريف واحد يقرأه الخادم والعميل.
 *
 * لا يوجد توجيه لغات في المسار (`/ar/...`): اللغة تفضيل مستخدم لا هوية
 * صفحة، وتخزينها في كوكي يعني أن كل رابط في التطبيق يبقى صالحًا ومشتركًا
 * بين اللغتين بدل أن يتضاعف.
 */

export const LOCALES = ["ar", "en"] as const;
export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "ar";
export const TIME_ZONE = "Africa/Cairo";

export const THEMES = ["light", "dark"] as const;
export type Theme = (typeof THEMES)[number];

/** الفاتح هو الافتراضي — لا نتبع تفضيل النظام إلا إن اختاره المستخدم صراحةً. */
export const DEFAULT_THEME: Theme = "light";

export const LOCALE_COOKIE = "ff_locale";
export const THEME_COOKIE = "ff_theme";

/** سنة كاملة: تفضيل عرض لا جلسة، ولا معنى لانتهائه مع الجلسة. */
export const PREFERENCE_MAX_AGE = 60 * 60 * 24 * 365;

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

export function isTheme(value: unknown): value is Theme {
  return typeof value === "string" && (THEMES as readonly string[]).includes(value);
}

export function directionOf(locale: Locale): "rtl" | "ltr" {
  return locale === "ar" ? "rtl" : "ltr";
}

/**
 * لغة التنسيق الرقمي.
 *
 * `-u-nu-latn` مقصود في العربية: الأرقام العربية-الهندية تُقرأ بصعوبة في
 * جداول غذائية وقياسات، ومعظم التطبيقات الطبية العربية تعرض الأرقام
 * اللاتينية مع النص العربي.
 */
export function numericLocale(locale: Locale): string {
  return locale === "ar" ? "ar-EG-u-nu-latn" : "en-GB";
}

export const LOCALE_LABELS: Record<Locale, string> = {
  ar: "العربية",
  en: "English",
};
