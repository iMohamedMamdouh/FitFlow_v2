import { getRequestConfig } from "next-intl/server";

/**
 * لغة واحدة حاليًا: العربية (ADR-004).
 *
 * الواجهة لا تحمل توجيهًا بلغات (`/ar/...`) عمدًا — إضافة مسار لغة واحدة
 * تعقيد بلا مقابل. `next-intl` موجودة رغم ذلك لأن كل نص في الواجهة يمر
 * عبر ملف الرسائل، فإضافة لغة ثانية لاحقًا تصبح ملف JSON جديدًا لا
 * مراجعة لكل مكوّن.
 */
export const LOCALE = "ar" as const;
export const TIME_ZONE = "Africa/Cairo";

export default getRequestConfig(async () => ({
  locale: LOCALE,
  timeZone: TIME_ZONE,
  messages: (await import("../../messages/ar.json")).default,
}));
