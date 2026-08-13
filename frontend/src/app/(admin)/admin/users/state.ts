/**
 * حالة نماذج لوحة المدير.
 *
 * في ملف مستقل لأن ملفات `"use server"` لا تصدّر إلا دوالّ غير متزامنة.
 *
 * `values` و`attempt` يحلّان مشكلة حقيقية: React يُعيد ضبط النموذج بعد
 * انتهاء الـ Server Action، فرفضٌ من الخادم — سلَج مكرّر مثلًا — كان يمحو
 * كل ما كتبه المدير في نموذج من عشرين حقلًا. الفعل يُرجع ما أُرسل،
 * و`attempt` يتغيّر مع كل محاولة فيُعاد تركيب النموذج بالقيم المعادة
 * (تغيير `defaultValue` وحده لا يؤثر على حقل مركَّب بالفعل).
 */

export type FormValues = Record<string, string[]>;

export type AdminActionState = {
  error: string | null;
  message: string | null;
  values: FormValues | null;
  attempt: number;
};

export const EMPTY_ADMIN_STATE: AdminActionState = {
  error: null,
  message: null,
  values: null,
  attempt: 0,
};

/** يلتقط ما أُرسل — بما فيه الحقول متعدّدة القيم مثل مسبّبات الحساسية. */
export function capture(form: FormData): FormValues {
  const values: FormValues = {};
  for (const [key, value] of form.entries()) {
    if (typeof value !== "string") continue;
    (values[key] ??= []).push(value);
  }
  return values;
}

export function textOf(values: FormValues | null, name: string, fallback: string): string {
  return values?.[name]?.[0] ?? fallback;
}

export function listOf(
  values: FormValues | null,
  name: string,
  fallback: readonly string[],
): readonly string[] {
  return values?.[name] ?? fallback;
}

/**
 * مربّع الاختيار غير المؤشَّر لا يُرسَل أصلًا، فغيابه من قيم محاولة سابقة
 * يعني "أُلغي تأشيره" لا "لم يُذكر" — ولذلك يُفحص وجود `values` أولًا.
 */
export function checkedOf(values: FormValues | null, name: string, fallback: boolean): boolean {
  if (values === null) return fallback;
  return (values[name]?.length ?? 0) > 0;
}
