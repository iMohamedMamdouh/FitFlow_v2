import { TIME_ZONE, numericLocale, type Locale } from "@/i18n/config";

/**
 * تنسيق موحّد للأرقام والتواريخ.
 *
 * كل قيمة رقمية في هذا النظام تصل من الـ API **كنص** لا كرقم: الخادم
 * يرسل `Decimal` كسلسلة حتى لا يفقد الدقة في تمثيل الفاصلة العائمة. لذلك
 * كل دالة هنا تقبل `string | number`، والتحويل يحدث في مكان واحد بدل أن
 * يتكرر `Number(x)` في كل مكوّن.
 *
 * الدوال تأخذ اللغة كمعامل صريح لا تقرؤها من سياق ضمني: نفس الدالة
 * تُستدعى من مكوّنات خادم وعميل، وتمرير اللغة يجعل الناتج واحدًا في
 * الاثنين — وهو شرط عدم اختلاف ما يُصيَّر على الخادم عمّا يُركَّب في
 * المتصفح.
 */

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatNumber(
  locale: Locale,
  value: string | number | null | undefined,
  fractionDigits = 0,
): string {
  const parsed = toNumber(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat(numericLocale(locale), {
    minimumFractionDigits: 0,
    maximumFractionDigits: fractionDigits,
  }).format(parsed);
}

/** الفرق بين قياسين، بإشارة صريحة — الإشارة هي المعلومة هنا. */
export function formatDelta(locale: Locale, value: number | null, fractionDigits = 1): string {
  if (value === null || !Number.isFinite(value)) return "—";
  const formatted = formatNumber(locale, Math.abs(value), fractionDigits);
  if (Math.abs(value) < 0.05) return formatted;
  return value > 0 ? `+${formatted}` : `−${formatted}`;
}

export function formatDate(locale: Locale, value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(numericLocale(locale), {
    dateStyle: "medium",
    timeZone: TIME_ZONE,
  }).format(date);
}

export function formatDateTime(locale: Locale, value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(numericLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: TIME_ZONE,
  }).format(date);
}

/**
 * تاريخ قصير لمحاور الرسوم.
 *
 * `Intl` بالعربية يدسّ علامات اتجاه (U+200F) داخل التاريخ. داخل نص SVG
 * — وهو محيط LTR دائمًا — تقلب هذه العلامات ترتيب الأجزاء فيظهر
 * "13/08/2026" كـ "132026/08/". نحذفها ونكتفي باليوم والشهر.
 */
export function formatAxisDate(locale: Locale, value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(numericLocale(locale), {
    day: "2-digit",
    month: "2-digit",
    timeZone: TIME_ZONE,
  })
    .format(date)
    .replace(/[\u200e\u200f\u061c]/gu, "");
}

export function formatTime(locale: Locale, value: Date): string {
  return new Intl.DateTimeFormat(numericLocale(locale), {
    timeStyle: "short",
    timeZone: TIME_ZONE,
  }).format(value);
}

/** تاريخ اليوم بصيغة ISO في توقيت القاهرة — لا في توقيت المتصفح. */
export function todayIso(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

/**
 * مؤشر كتلة الجسم يُحسب ولا يُخزَّن — نفس قرار قاعدة البيانات، لأن قيمة
 * محفوظة تصبح خاطئة بمجرد تغيّر الوزن أو الطول.
 */
export function bodyMassIndex(
  weightKg: string | number | null | undefined,
  heightCm: string | number | null | undefined,
): number | null {
  const weight = toNumber(weightKg);
  const height = toNumber(heightCm);
  if (weight === null || height === null || height <= 0) return null;
  const meters = height / 100;
  return weight / (meters * meters);
}

export { toNumber };
