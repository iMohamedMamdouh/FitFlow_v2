"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import { capture, type AdminActionState } from "../users/state";

/**
 * تعديل القاعدة العلمية.
 *
 * قاعدتان مشتركتان بين الثلاثة كيانات:
 *
 * 1. **لا حذف.** التعطيل حقل في النموذج نفسه، ولا يوجد فعل حذف أصلًا —
 *    الخطط المولَّدة تشير إلى هذا المحتوى.
 * 2. **الإنشاء والتعديل نفس النموذج.** الفرق معرّف موجود أو لا، فلا
 *    يفترقان في التحقق ولا في الحقول المطلوبة.
 */

function invalidPhases(message: string, state: AdminActionState, form: FormData): AdminActionState {
  return { error: message, message: null, values: capture(form), attempt: state.attempt + 1 };
}

function refresh(): void {
  revalidatePath("/admin/catalog/foods");
  revalidatePath("/admin/catalog/exercises");
  revalidatePath("/admin/catalog/injuries");
  revalidatePath("/admin");
}

async function failure(
  error: unknown,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const apiError = toApiError(error);
  const t = await getTranslations("errors");
  return {
    error: apiError.detail ?? t(apiError.key),
    message: null,
    values: capture(form),
    attempt: state.attempt + 1,
  };
}

function text(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value.trim() : "";
}

function optional(form: FormData, name: string): string | null {
  return text(form, name) || null;
}

/** قائمة مفصولة بفواصل — الشكل الوحيد الذي يكتبه إنسان في حقل واحد. */
function list(form: FormData, name: string): string[] {
  return text(form, name)
    .split(/[,،]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function save(
  path: string,
  id: string | null,
  body: unknown,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.catalog");
  try {
    await apiFetch(id === null ? path : `${path}/${id}`, {
      method: id === null ? "POST" : "PATCH",
      body,
    });
    refresh();
    // النجاح يترك النموذج فارغًا عمدًا في حالة الإضافة: احتفاظه بالقيم
    // بعد الحفظ يغري بإرسال نسخة ثانية من نفس العنصر.
    return {
      error: null,
      message: t(id === null ? "created" : "saved"),
      values: null,
      attempt: state.attempt + 1,
    };
  } catch (error) {
    return failure(error, state, form);
  }
}

export async function saveFoodAction(
  id: string | null,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  return save(
    "/admin/catalog/foods",
    id,
    {
      name_ar: text(form, "name_ar"),
      name_en: optional(form, "name_en"),
      category: text(form, "category"),
      calories_per_100g: text(form, "calories_per_100g"),
      protein_g: text(form, "protein_g"),
      carbs_g: text(form, "carbs_g"),
      fat_g: text(form, "fat_g"),
      fiber_g: text(form, "fiber_g") || "0",
      allergens: form.getAll("allergens").map(String),
      is_active: form.get("is_active") === "on",
    },
    state,
    form,
  );
}

export async function saveExerciseAction(
  id: string | null,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  return save(
    "/admin/catalog/exercises",
    id,
    {
      name_ar: text(form, "name_ar"),
      name_en: optional(form, "name_en"),
      slug: text(form, "slug"),
      category: text(form, "category"),
      difficulty: text(form, "difficulty"),
      primary_region: text(form, "primary_region"),
      target_muscles: list(form, "target_muscles"),
      equipment: list(form, "equipment"),
      instructions_ar: optional(form, "instructions_ar"),
      video_url: optional(form, "video_url"),
      is_active: form.get("is_active") === "on",
    },
    state,
    form,
  );
}

export async function saveInjuryTypeAction(
  id: string | null,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.catalog");

  // المراحل بروتوكول مركّب يُكتب JSON. الفحص هنا لا في الخادم وحده:
  // الخادم يردّ 422 عامة، وهذه الرسالة تقول أي حقل بالضبط.
  let phases: unknown = [];
  const raw = text(form, "phases");
  if (raw !== "") {
    try {
      phases = JSON.parse(raw);
    } catch {
      return invalidPhases(t("phasesInvalid"), state, form);
    }
    if (!Array.isArray(phases)) return invalidPhases(t("phasesInvalid"), state, form);
  }

  return save(
    "/admin/catalog/injury-types",
    id,
    {
      name_ar: text(form, "name_ar"),
      name_en: optional(form, "name_en"),
      slug: text(form, "slug"),
      body_region: text(form, "body_region"),
      description_ar: optional(form, "description_ar"),
      phases,
      is_active: form.get("is_active") === "on",
    },
    state,
    form,
  );
}

export async function recordReviewAction(
  kind: "exercises" | "injury-types",
  id: string,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.catalog");
  try {
    await apiFetch(`/admin/catalog/${kind}/${id}/review`, {
      method: "POST",
      body: {
        reviewed_by: text(form, "reviewed_by"),
        source_reference: text(form, "source_reference"),
      },
    });
    refresh();
    return { error: null, message: t("reviewSaved"), values: null, attempt: state.attempt + 1 };
  } catch (error) {
    return failure(error, state, form);
  }
}
