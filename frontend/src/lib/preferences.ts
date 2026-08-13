import "server-only";

import { cookies } from "next/headers";

import {
  DEFAULT_LOCALE,
  DEFAULT_THEME,
  LOCALE_COOKIE,
  THEME_COOKIE,
  isLocale,
  isTheme,
  type Locale,
  type Theme,
} from "@/i18n/config";

/**
 * قراءة تفضيلات العرض على الخادم.
 *
 * قراءة المظهر على الخادم — لا في سكربت يعمل بعد التحميل — هي ما يمنع
 * وميض الوضع الخطأ: الصفحة تصل للمتصفح ومعها `data-theme` الصحيح على
 * `<html>` من أول بايت.
 */

export async function readLocale(): Promise<Locale> {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export async function readTheme(): Promise<Theme> {
  const value = (await cookies()).get(THEME_COOKIE)?.value;
  return isTheme(value) ? value : DEFAULT_THEME;
}
