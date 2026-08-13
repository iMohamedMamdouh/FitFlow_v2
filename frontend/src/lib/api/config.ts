/**
 * عنوان الـ API.
 *
 * `API_URL` (خادمي فقط) يسبق `NEXT_PUBLIC_API_URL`: الواجهة لا تنادي
 * الخادم من المتصفح إطلاقًا، فلا داعي لتسريب العنوان الداخلي إلى الحزمة
 * المُرسَلة للمتصفح. المتغيّر العام يبقى مدعومًا لأنه موجود في
 * `.env.example` منذ المرحلة 0 ولأن نشر Docker يستخدمه.
 */
export function apiBaseUrl(): string {
  const url = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  return url.replace(/\/+$/u, "");
}

export const API_PREFIX = "/api/v1";
