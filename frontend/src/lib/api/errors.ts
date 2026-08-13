/**
 * معالجة أخطاء موحّدة (الخطوة 7.2).
 *
 * الخادم يرسل رسائله بالعربية بالفعل في الحالات التي كتبناها (`detail`
 * نصية)، لكن ثلاث حالات لا يغطيها ذلك: أخطاء الشبكة قبل الوصول للخادم،
 * وأخطاء التحقق التي تصل كمصفوفة `loc/msg` غير مفهومة للمستخدم، وأخطاء
 * لم نكتب لها نصًا. الترجمة هنا تضمن أن **كل** طريق ينتهي برسالة عربية
 * واحدة قابلة للعرض، فلا يظهر `[object Object]` في أي شاشة.
 */

export const ERROR_KEYS = [
  "network",
  "unauthorized",
  "forbidden",
  "notFound",
  "conflict",
  "validation",
  "tooLarge",
  "server",
  "unknown",
] as const;

export type ErrorKey = (typeof ERROR_KEYS)[number];

export class ApiError extends Error {
  readonly status: number;
  readonly key: ErrorKey;
  /** رسالة الخادم كما وصلت — تُعرض عند وجودها لأنها أدق من العامة. */
  readonly detail: string | null;

  constructor(status: number, key: ErrorKey, detail: string | null) {
    super(detail ?? key);
    this.name = "ApiError";
    this.status = status;
    this.key = key;
    this.detail = detail;
  }

  static network(): ApiError {
    return new ApiError(0, "network", null);
  }
}

function keyForStatus(status: number): ErrorKey {
  if (status === 401) return "unauthorized";
  if (status === 403) return "forbidden";
  if (status === 404) return "notFound";
  if (status === 409) return "conflict";
  if (status === 413) return "tooLarge";
  if (status === 422) return "validation";
  if (status >= 500) return "server";
  return "unknown";
}

type ValidationEntry = { readonly msg?: unknown; readonly loc?: unknown };

/**
 * يستخرج نصًا صالحًا للعرض من جسم الخطأ.
 *
 * FastAPI يرسل `detail` نصية للأخطاء التي نرفعها بأنفسنا، ومصفوفة كائنات
 * لأخطاء التحقق التلقائية. الحالتان تُعالجان هنا، وأي شكل آخر يُهمَل بدل
 * أن يُعرض كما هو.
 */
function extractDetail(body: unknown): string | null {
  if (typeof body !== "object" || body === null) return null;
  const detail = (body as { detail?: unknown }).detail;

  if (typeof detail === "string" && detail.trim() !== "") return detail;

  if (Array.isArray(detail)) {
    const messages = (detail as ValidationEntry[])
      .map((entry) => (typeof entry.msg === "string" ? entry.msg : null))
      .filter((message): message is string => message !== null);
    // رسائل pydantic تأتي أحيانًا مسبوقة بـ "Value error, " من المحرّك نفسه.
    const cleaned = messages.map((message) => message.replace(/^Value error,\s*/u, ""));
    if (cleaned.length > 0) return cleaned.join(" • ");
  }

  return null;
}

export async function apiErrorFromResponse(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // رد بلا جسم JSON (502 من بروكسي مثلًا) — الحالة وحدها تكفي.
  }
  return new ApiError(response.status, keyForStatus(response.status), extractDetail(body));
}

/** كل ما قد يُرمى في الواجهة يتحوّل إلى `ApiError` واحد. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (error instanceof TypeError) return ApiError.network();
  return new ApiError(0, "unknown", null);
}
