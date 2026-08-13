"use server";

import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { apiFetch } from "@/lib/api/server";
import { ApiError, toApiError } from "@/lib/api/errors";
import type { TokenPair, UserPublic } from "@/lib/api/schema";
import { clearSession, readRefreshToken, saveSession } from "@/lib/auth/session";
import type { AuthState } from "@/lib/auth/state";

/**
 * تسجيل الدخول والتسجيل والخروج (الخطوة 7.3).
 *
 * الأفعال هنا هي الوحيدة التي ترى رموز الجلسة. تُنفَّذ على الخادم، فلا
 * يصل الرمز إلى المتصفح إلا داخل كوكي `httpOnly` لا يقرؤه JavaScript.
 */

/** المسار التالي يُقبل فقط لو داخليًا — قيمة من الرابط لا يجوز أن تصبح تحويلًا لموقع آخر. */
function safeNext(value: FormDataEntryValue | null): string {
  if (typeof value !== "string") return "/dashboard";
  if (!value.startsWith("/") || value.startsWith("//")) return "/dashboard";
  return value;
}

function text(form: FormData, key: string): string {
  const value = form.get(key);
  return typeof value === "string" ? value.trim() : "";
}

async function messageFor(error: ApiError): Promise<string> {
  const t = await getTranslations("errors");
  // رسالة الخادم أدق من العامة حين توجد — وهي بالعربية أصلًا.
  return error.detail ?? t(error.key);
}

export async function loginAction(_state: AuthState, form: FormData): Promise<AuthState> {
  const email = text(form, "email");
  const password = text(form, "password");
  const next = safeNext(form.get("next"));

  try {
    const tokens = await apiFetch<TokenPair>("/auth/login", {
      method: "POST",
      body: { email, password },
      anonymous: true,
    });
    await saveSession(tokens);
  } catch (error) {
    const apiError = toApiError(error);
    if (apiError.status === 401) {
      const t = await getTranslations("auth");
      return { error: t("invalidCredentials") };
    }
    return { error: await messageFor(apiError) };
  }

  redirect(next);
}

export async function registerAction(_state: AuthState, form: FormData): Promise<AuthState> {
  const email = text(form, "email");
  const password = text(form, "password");
  const fullName = text(form, "full_name");

  const t = await getTranslations("auth");
  if (fullName.length < 2) return { error: t("nameTooShort") };
  if (password.length < 12) return { error: t("weakPassword") };

  try {
    await apiFetch<UserPublic>("/auth/register", {
      method: "POST",
      body: { email, password, full_name: fullName },
      anonymous: true,
    });
    const tokens = await apiFetch<TokenPair>("/auth/login", {
      method: "POST",
      body: { email, password },
      anonymous: true,
    });
    await saveSession(tokens);
  } catch (error) {
    const apiError = toApiError(error);
    if (apiError.status === 409) return { error: t("emailTaken") };
    return { error: await messageFor(apiError) };
  }

  // التسجيل ينتهي دائمًا عند التنبيه الطبي: لا خطوة أخرى قبل الموافقة.
  redirect("/onboarding");
}

export async function logoutAction(): Promise<void> {
  const refreshToken = await readRefreshToken();
  if (refreshToken !== null) {
    try {
      await apiFetch<void>("/auth/logout", {
        method: "POST",
        body: { refresh_token: refreshToken },
        anonymous: true,
      });
    } catch {
      // إبطال الرمز على الخادم قد يفشل (شبكة، رمز منتهٍ) — لكن حذف
      // الكوكي محليًا يجب أن يحدث في كل الأحوال، وإلا بقي المستخدم داخلًا.
    }
  }
  await clearSession();
  redirect("/login");
}
