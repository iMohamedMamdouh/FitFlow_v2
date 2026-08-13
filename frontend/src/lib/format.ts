import { LOCALE, TIME_ZONE } from "@/i18n/request";

/**
 * تنسيق موحّد للأرقام والتواريخ.
 *
 * كل قيمة رقمية في هذا النظام تصل من الـ API **كنص** لا كرقم: الخادم
 * يرسل `Decimal` كسلسلة حتى لا يفقد الدقة في تمثيل الفاصلة العائمة. لذلك
 * كل دالة هنا تقبل `string | number`، والتحويل يحدث في مكان واحد بدل أن
 * يتكرر `Number(x)` في كل مكوّن.
 */

const NUMERIC_LOCALE = `${LOCALE}-EG-u-nu-latn`;

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatNumber(
  value: string | number | null | undefined,
  fractionDigits = 0,
): string {
  const parsed = toNumber(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat(NUMERIC_LOCALE, {
    minimumFractionDigits: 0,
    maximumFractionDigits: fractionDigits,
  }).format(parsed);
}

/** الفرق بين قياسين، بإشارة صريحة — الإشارة هي المعلومة هنا. */
export function formatDelta(value: number | null, fractionDigits = 1): string {
  if (value === null || !Number.isFinite(value)) return "—";
  const formatted = formatNumber(Math.abs(value), fractionDigits);
  if (Math.abs(value) < 0.05) return formatted;
  return value > 0 ? `+${formatted}` : `−${formatted}`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(NUMERIC_LOCALE, {
    dateStyle: "medium",
    timeZone: TIME_ZONE,
  }).format(date);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(NUMERIC_LOCALE, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: TIME_ZONE,
  }).format(date);
}

export function formatTime(value: Date): string {
  return new Intl.DateTimeFormat(NUMERIC_LOCALE, {
    timeStyle: "short",
    timeZone: TIME_ZONE,
  }).format(value);
}

/** تاريخ اليوم بصيغة ISO في توقيت القاهرة — لا في توقيت المتصفح. */
export function todayIso(): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  return parts;
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
