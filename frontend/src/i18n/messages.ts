import ar from "../../messages/ar.json";
import en from "../../messages/en.json";

import type { Locale } from "./config";

/**
 * ملفات الرسائل، بفحص تطابق على مستوى الأنواع.
 *
 * `satisfies Record<Locale, typeof ar>` يعني أن أي مفتاح موجود في العربية
 * وناقص في الإنجليزية يفشل عند `tsc --noEmit` — لا في شاشة أمام مستخدم
 * يرى مسار المفتاح مكان النص.
 */
const MESSAGES = { ar, en } satisfies Record<Locale, typeof ar>;

export function messagesFor(locale: Locale): typeof ar {
  return MESSAGES[locale];
}

/**
 * مفاتيح أفعال سجل التدقيق.
 *
 * الفعل يصل من الخادم كنص حر (`"plan.approved"`)، وnext-intl لا يقبل
 * نصًا غير معروف كمفتاح. الاشتقاق من ملف الرسائل نفسه — لا قائمة يدوية
 * موازية — يعني أن المفاتيح المقبولة هي بالضبط ما له ترجمة، ولا يوجد
 * مكانان يمكن أن يتباعدا.
 *
 * **النقطة فاصل مجالات في next-intl لا جزءًا من المفتاح.** لذلك
 * `auditActions` مُعشَّشة (`plan.approved` = `plan` ثم `approved`)؛
 * المفتاح المسطّح `"plan.approved"` يبدو صالحًا في JSON ثم لا يُحلّ
 * إطلاقًا وقت التشغيل.
 */
type AuditActions = (typeof ar)["auditActions"];

export type AuditActionKey = {
  [Group in keyof AuditActions & string]: `${Group}.${keyof AuditActions[Group] & string}`;
}[keyof AuditActions & string];

export function isAuditActionKey(value: string): value is AuditActionKey {
  const [group, action] = value.split(".");
  if (group === undefined || action === undefined) return false;
  const bucket = (ar.auditActions as Record<string, Record<string, string>>)[group];
  return bucket !== undefined && Object.hasOwn(bucket, action);
}
