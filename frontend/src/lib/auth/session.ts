import "server-only";

import { cookies } from "next/headers";

import type { TokenPair } from "@/lib/api/schema";

/**
 * الجلسة تعيش في كوكيز `httpOnly` — لا في `localStorage`.
 *
 * رموز الوصول في `localStorage` يقرأها أي سكربت يعمل في الصفحة، فأي ثغرة
 * XSS واحدة تتحول إلى سرقة كاملة لحساب مريض. الكوكي `httpOnly` غير مرئي
 * لـ JavaScript أصلًا، وثمن ذلك أن كل نداء للـ API يتم من الخادم —
 * وهو ما تفعله هذه الواجهة بالكامل.
 *
 * `SameSite=Lax` كافٍ هنا لأن كل الكتابات تمر عبر Server Actions، وهي
 * طلبات POST محمية بتوقيع Next نفسه.
 */

export const ACCESS_COOKIE = "ff_at";
export const REFRESH_COOKIE = "ff_rt";
export const EXPIRES_COOKIE = "ff_exp";

/** يُجدَّد الرمز قبل انتهائه بهامش، لا بعده — التجديد بعد الفشل يعني طلبًا ضائعًا. */
export const REFRESH_MARGIN_MS = 120_000;

const SECURE = process.env.NODE_ENV === "production";

export type SessionCookie = { name: string; value: string; maxAge: number };

export const COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: "lax",
  secure: SECURE,
  path: "/",
} as const;

/**
 * يحوّل زوج الرموز إلى كوكيز جاهزة للكتابة.
 *
 * دالة نقية بلا `next/headers` عمدًا: الـ middleware يكتب على الاستجابة
 * مباشرة ولا يستطيع استخدام واجهة الكوكيز الخاصة بمكوّنات الخادم.
 */
export function sessionCookies(tokens: TokenPair, refreshDays = 14): SessionCookie[] {
  const accessMaxAge = Math.max(
    60,
    Math.floor((new Date(tokens.expires_at).getTime() - Date.now()) / 1000),
  );
  return [
    { name: ACCESS_COOKIE, value: tokens.access_token, maxAge: accessMaxAge },
    { name: REFRESH_COOKIE, value: tokens.refresh_token, maxAge: refreshDays * 24 * 60 * 60 },
    {
      name: EXPIRES_COOKIE,
      value: String(new Date(tokens.expires_at).getTime()),
      maxAge: refreshDays * 24 * 60 * 60,
    },
  ];
}

export const SESSION_COOKIE_NAMES = [ACCESS_COOKIE, REFRESH_COOKIE, EXPIRES_COOKIE] as const;

export async function saveSession(tokens: TokenPair): Promise<void> {
  const store = await cookies();
  for (const cookie of sessionCookies(tokens)) {
    store.set(cookie.name, cookie.value, { ...COOKIE_OPTIONS, maxAge: cookie.maxAge });
  }
}

export async function clearSession(): Promise<void> {
  const store = await cookies();
  for (const name of SESSION_COOKIE_NAMES) {
    store.delete(name);
  }
}

export async function readAccessToken(): Promise<string | null> {
  return (await cookies()).get(ACCESS_COOKIE)?.value ?? null;
}

export async function readRefreshToken(): Promise<string | null> {
  return (await cookies()).get(REFRESH_COOKIE)?.value ?? null;
}

export async function hasSession(): Promise<boolean> {
  return (await readAccessToken()) !== null;
}
