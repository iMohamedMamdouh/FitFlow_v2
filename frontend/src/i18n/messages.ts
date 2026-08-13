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
