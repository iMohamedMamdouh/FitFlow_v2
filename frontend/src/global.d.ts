import type messages from "../messages/ar.json";

/**
 * تعريف مفاتيح الرسائل لـ TypeScript.
 *
 * بدونه، `t("typo.key")` خطأ يظهر وقت التشغيل فقط — نص مفقود في شاشة
 * أمام مستخدم. مع هذا التعريف يفشل `tsc --noEmit` على أي مفتاح غير موجود،
 * فيصير الخطأ مستحيلًا لا نادرًا.
 */
declare module "next-intl" {
  interface AppConfig {
    Messages: typeof messages;
  }
}
