import { NextResponse, type NextRequest } from "next/server";

import { API_PREFIX, apiBaseUrl } from "@/lib/api/config";
import {
  ACCESS_COOKIE,
  COOKIE_OPTIONS,
  EXPIRES_COOKIE,
  REFRESH_COOKIE,
  REFRESH_MARGIN_MS,
  SESSION_COOKIE_NAMES,
  sessionCookies,
} from "@/lib/auth/session";
import type { TokenPair } from "@/lib/api/schema";

/**
 * حماية المسارات وتجديد الرمز (الخطوة 7.3).
 *
 * التجديد يحدث هنا لا في كل نداء، والسبب في الخادم: رمز التحديث **يدور**،
 * واستخدام رمز سبق تدويره يُفسَّر كتسريب فيُبطل كل جلسات المستخدم. لو
 * جدّد كل نداء بمفرده لتسابقت نداءات متوازية على نفس الرمز وخرج المستخدم
 * من حسابه بلا سبب ظاهر.
 *
 * لذلك: التجديد في مكان واحد، **وقبل** الانتهاء بهامش، **ومستبعَد منه
 * طلبات الـ prefetch** لأنها وحدها ما قد يصل متوازيًا من متصفح واحد.
 */

const PUBLIC_PATHS = ["/", "/login", "/register"] as const;

function isPublic(pathname: string): boolean {
  return (PUBLIC_PATHS as readonly string[]).includes(pathname);
}

function isPrefetch(request: NextRequest): boolean {
  return (
    request.headers.get("next-router-prefetch") === "1" ||
    request.headers.get("purpose") === "prefetch" ||
    request.headers.get("x-purpose") === "prefetch"
  );
}

function needsRefresh(request: NextRequest): boolean {
  const expiresAt = Number(request.cookies.get(EXPIRES_COOKIE)?.value ?? "");
  if (!Number.isFinite(expiresAt)) return true;
  return Date.now() > expiresAt - REFRESH_MARGIN_MS;
}

async function rotateTokens(refreshToken: string): Promise<TokenPair | null> {
  try {
    const response = await fetch(`${apiBaseUrl()}${API_PREFIX}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!response.ok) return null;
    return (await response.json()) as TokenPair;
  } catch {
    // الخادم غير متاح: نُبقي الرمز الحالي بدل إخراج المستخدم. لو كان
    // منتهيًا فعلًا سيرد الـ API بـ 401 وتُعالَج الحالة في مكانها.
    return null;
  }
}

function redirectToLogin(request: NextRequest): NextResponse {
  const url = new URL("/login", request.url);
  const target = request.nextUrl.pathname + request.nextUrl.search;
  if (target !== "/") url.searchParams.set("next", target);

  const response = NextResponse.redirect(url);
  for (const name of SESSION_COOKIE_NAMES) response.cookies.delete(name);
  return response;
}

export default async function proxy(request: NextRequest): Promise<NextResponse> {
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  const pathname = request.nextUrl.pathname;
  const authenticated = accessToken !== undefined || refreshToken !== undefined;

  if (!authenticated) {
    return isPublic(pathname) ? NextResponse.next() : redirectToLogin(request);
  }

  // صفحات الدخول والتسجيل لا معنى لها لمن سجّل دخوله بالفعل.
  if (pathname === "/login" || pathname === "/register") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (refreshToken === undefined) {
    return accessToken === undefined ? redirectToLogin(request) : NextResponse.next();
  }

  if (isPrefetch(request) || !needsRefresh(request)) {
    return NextResponse.next();
  }

  const tokens = await rotateTokens(refreshToken);
  if (tokens === null) {
    // رمز التحديث نفسه مرفوض — الجلسة انتهت فعلًا.
    return isPublic(pathname) ? NextResponse.next() : redirectToLogin(request);
  }

  const fresh = sessionCookies(tokens);
  // الكوكي يُكتب على الطلب **و** على الاستجابة: الأول ليراه هذا الـ render
  // نفسه، والثاني ليصل المتصفح للطلبات التالية.
  for (const cookie of fresh) request.cookies.set(cookie.name, cookie.value);

  const response = NextResponse.next({ request });
  for (const cookie of fresh) {
    response.cookies.set(cookie.name, cookie.value, {
      ...COOKIE_OPTIONS,
      maxAge: cookie.maxAge,
    });
  }
  return response;
}

export const config = {
  // نستثني الملفات الساكنة وصور Next — تمريرها على الـ middleware يضيف
  // زمنًا على كل أصل بلا فائدة.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|webp|ico)$).*)"],
};
