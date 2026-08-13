"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

import { LOCALE_COOKIE, PREFERENCE_MAX_AGE, isLocale } from "@/i18n/config";

/**
 * تبديل اللغة.
 *
 * فعل خادمي لأن تغيير اللغة يغيّر نصًا مُصيَّرًا على الخادم واتجاه الصفحة
 * معًا — لا يكفي فيه تبديل صنف في المتصفح. (المظهر عكسه: يُبدَّل في
 * المتصفح مباشرة لأنه ألوان فقط.)
 *
 * الكوكي **ليس** `httpOnly`: لا يحمل أي معلومة عن الحساب، وقراءته من
 * المتصفح تفيد في إبقاء الاختيار ظاهرًا فورًا.
 */
export async function setLocaleAction(value: string): Promise<void> {
  if (!isLocale(value)) return;

  (await cookies()).set(LOCALE_COOKIE, value, {
    httpOnly: false,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: PREFERENCE_MAX_AGE,
  });
  revalidatePath("/", "layout");
}
