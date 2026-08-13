"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { ApiError, toApiError } from "@/lib/api/errors";
import { apiFetch, apiFetchOrNull } from "@/lib/api/server";
import type { ProfileRead, ProfileUpsert } from "@/lib/api/schema";
import { todayIso } from "@/lib/format";
import { STEPS, type Step, type StepState } from "./steps";

/**
 * حفظ خطوات الـ Onboarding (الخطوة 7.4).
 *
 * كل خطوة تُحفظ عند الانتقال منها، لا في النهاية: نموذج من أربع خطوات
 * يُفقد بالكامل عند إغلاق التبويب هو أسوأ ما يمكن أن يقابل مستخدمًا
 * جديدًا. ولأن `PUT /me/profile` استبدال كامل لا تعديل جزئي، كل خطوة
 * تقرأ الحالة المخزَّنة أولًا وتدمج حقولها فوقها.
 */

function text(form: FormData, key: string): string {
  const value = form.get(key);
  return typeof value === "string" ? value.trim() : "";
}

/** سطر واحد = بند واحد. الأسطر الفارغة تُهمَل بدل أن تُخزَّن كبنود بلا محتوى. */
function lines(form: FormData, key: string): string[] {
  return text(form, key)
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "");
}

/** يبني الحمولة الكاملة من الملف المخزَّن ثم يضع فوقها حقول الخطوة الحالية. */
function merge(profile: ProfileRead | null, patch: Partial<ProfileUpsert>): ProfileUpsert {
  return {
    birth_date: patch.birth_date ?? profile?.birth_date ?? "",
    gender: patch.gender ?? profile?.gender ?? "male",
    height_cm: patch.height_cm ?? profile?.height_cm ?? "0",
    activity_level: patch.activity_level ?? profile?.activity_level ?? "sedentary",
    goal: patch.goal ?? profile?.goal ?? "maintenance",
    medical_history: patch.medical_history ?? profile?.medical_history ?? [],
    chronic_diseases: patch.chronic_diseases ?? profile?.chronic_diseases ?? [],
    medications: patch.medications ?? profile?.medications ?? [],
    allergens: patch.allergens ?? profile?.allergens ?? [],
    notes: patch.notes ?? profile?.notes ?? null,
  };
}

function patchFor(step: Step, form: FormData): Partial<ProfileUpsert> {
  switch (step) {
    case "personal":
      return {
        birth_date: text(form, "birth_date"),
        gender: text(form, "gender") as ProfileUpsert["gender"],
        height_cm: text(form, "height_cm"),
      };
    case "medical":
      return {
        medical_history: lines(form, "medical_history"),
        chronic_diseases: lines(form, "chronic_diseases"),
        medications: lines(form, "medications"),
        notes: text(form, "notes") || null,
      };
    case "goals":
      return {
        goal: text(form, "goal") as ProfileUpsert["goal"],
        activity_level: text(form, "activity_level") as ProfileUpsert["activity_level"],
      };
    case "allergies":
      return {
        allergens: form
          .getAll("allergens")
          .filter(
            (value): value is string => typeof value === "string",
          ) as ProfileUpsert["allergens"],
      };
  }
}

/**
 * الوزن لا يُخزَّن في الملف الشخصي — مكانه سلسلة القياسات (قرار المرحلة 2).
 * لذلك خطوة البيانات الشخصية تكتب قياسًا لا حقلًا.
 */
async function recordInitialWeight(weight: string): Promise<void> {
  if (weight === "") return;
  try {
    await apiFetch("/me/readings", {
      method: "POST",
      body: { reading_date: todayIso(), weight_kg: weight, source: "manual" },
    });
  } catch (error) {
    // 409 = سجّل وزنه اليوم بالفعل. الرجوع لخطوة سابقة وحفظها من جديد
    // حالة طبيعية تمامًا، فلا تُعرض كخطأ.
    if (!(error instanceof ApiError) || error.status !== 409) throw error;
  }
}

export async function saveStepAction(
  step: Step,
  _state: StepState,
  form: FormData,
): Promise<StepState> {
  const advance = form.get("advance") === "1";

  try {
    const profile = await apiFetchOrNull<ProfileRead>("/me/profile");
    await apiFetch<ProfileRead>("/me/profile", {
      method: "PUT",
      body: merge(profile, patchFor(step, form)),
    });
    if (step === "personal") await recordInitialWeight(text(form, "weight_kg"));
  } catch (error) {
    const apiError = toApiError(error);
    const t = await getTranslations("errors");
    return { error: apiError.detail ?? t(apiError.key), savedAt: null };
  }

  revalidatePath("/onboarding");
  if (!advance) return { error: null, savedAt: Date.now() };

  const nextIndex = STEPS.indexOf(step) + 1;
  const nextStep = STEPS[nextIndex];
  redirect(nextStep === undefined ? "/consent" : `/onboarding?step=${nextStep}`);
}
