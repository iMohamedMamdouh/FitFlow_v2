import "server-only";

import { API_PREFIX, apiBaseUrl } from "./config";
import { ApiError, apiErrorFromResponse, toApiError } from "./errors";
import { readAccessToken } from "@/lib/auth/session";

/**
 * كل نداء للـ API يمر من هنا (الخطوة 7.2).
 *
 * ثلاثة قرارات مثبَّتة في هذا الملف:
 *
 * 1. **الطلبات كلها من الخادم.** المتصفح لا يرى رمز الوصول ولا عنوان الـ
 *    API. الثمن أن كل قراءة تحدث في Server Component وكل كتابة في Server
 *    Action — وهو ثمن مقبول مقابل ألا يوجد رمز في `localStorage`.
 * 2. **لا تخزين مؤقت افتراضيًا.** `cache: "no-store"` مقصود: صفحة تعرض
 *    خطة مريض أو قياساته لا يجوز أن تُخدَم من ذاكرة مشتركة.
 * 3. **الخطأ نوع واحد.** كل مسار فشل ينتهي بـ `ApiError`، فلا يحتاج أي
 *    مستدعٍ أن يفحص `response.ok` بنفسه.
 */

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  /** لرفع الملفات — يُرسَل كما هو دون ترويسة `Content-Type` (المتصفح يضيف الحد الفاصل). */
  formData?: FormData;
  /** طلب بلا مصادقة (تسجيل الدخول مثلًا). */
  anonymous?: boolean;
  signal?: AbortSignal;
};

async function request(path: string, options: RequestOptions = {}): Promise<Response> {
  const headers = new Headers();
  if (!options.anonymous) {
    const token = await readAccessToken();
    if (token === null) throw new ApiError(401, "unauthorized", null);
    headers.set("Authorization", `Bearer ${token}`);
  }

  let body: BodyInit | undefined;
  if (options.formData !== undefined) {
    body = options.formData;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  try {
    return await fetch(`${apiBaseUrl()}${API_PREFIX}${path}`, {
      method: options.method ?? "GET",
      headers,
      body,
      cache: "no-store",
      signal: options.signal,
    });
  } catch (error) {
    throw toApiError(error);
  }
}

/** ينفّذ الطلب ويرجّع الجسم مفكوكًا، أو يرمي `ApiError`. */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await request(path, options);
  if (!response.ok) throw await apiErrorFromResponse(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/**
 * نسخة تتسامح مع 404.
 *
 * الملف الشخصي غير المستكمل و"لا توجد إصابات" حالتان طبيعيتان يرد عليهما
 * الخادم بـ 404. معاملتهما كخطأ تعني شاشة خطأ لمستخدم جديد لم يخطئ.
 */
export async function apiFetchOrNull<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T | null> {
  try {
    return await apiFetch<T>(path, options);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** ينزّل محتوى ثنائيًا (المرفقات الطبية) بدل فك JSON. */
export async function apiFetchBlob(path: string): Promise<{ body: ArrayBuffer; type: string }> {
  const response = await request(path);
  if (!response.ok) throw await apiErrorFromResponse(response);
  return {
    body: await response.arrayBuffer(),
    type: response.headers.get("content-type") ?? "application/octet-stream",
  };
}
