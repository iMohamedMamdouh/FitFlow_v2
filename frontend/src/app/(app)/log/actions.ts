"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { ApiError, toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { DailyLogRead, ReadingRead } from "@/lib/api/schema";
import type { LogState } from "./state";

function text(form: FormData, key: string): string {
  const value = form.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function optionalNumber(form: FormData, key: string): string | null {
  const value = text(form, key);
  return value === "" ? null : value;
}

/**
 * التسجيل اليومي (الخطوة 7.7).
 *
 * الوزن يُكتب مرتين عمدًا: في سجل اليوم (سياق يومي مع الألم والالتزام)
 * وفي سلسلة القياسات (`/me/readings`) لأنها المصدر الذي يقرأ منه محرك
 * القواعد الوزن الحالي ويكشف الثبات. الاكتفاء بالأول يعني تسجيلًا يوميًا
 * لا يؤثر في الخطة إطلاقًا.
 */
export async function saveDailyLogAction(_state: LogState, form: FormData): Promise<LogState> {
  const t = await getTranslations("log");
  const errors = await getTranslations("errors");

  const logDate = text(form, "log_date");
  const weight = optionalNumber(form, "weight_kg");
  const payload = {
    log_date: logDate,
    weight_kg: weight,
    pain_level: optionalNumber(form, "pain_level"),
    diet_adherence_pct: optionalNumber(form, "diet_adherence_pct"),
    exercise_adherence_pct: optionalNumber(form, "exercise_adherence_pct"),
    notes: text(form, "notes") || null,
  };

  if (
    payload.weight_kg === null &&
    payload.pain_level === null &&
    payload.diet_adherence_pct === null &&
    payload.exercise_adherence_pct === null
  ) {
    return { error: t("needOneValue"), message: null };
  }

  try {
    await apiFetch<DailyLogRead>("/me/logs", { method: "POST", body: payload });
  } catch (error) {
    const apiError = toApiError(error);
    if (apiError.status === 409) return { error: t("alreadyLogged"), message: null };
    return { error: apiError.detail ?? errors(apiError.key), message: null };
  }

  if (weight !== null) {
    try {
      await apiFetch<ReadingRead>("/me/readings", {
        method: "POST",
        body: { reading_date: logDate, weight_kg: weight, source: "manual" },
      });
    } catch (error) {
      // القياس مسجَّل بالفعل لهذا اليوم: السجل اليومي نجح، فلا داعي لإفزاع
      // المستخدم برسالة خطأ عن عملية ثانوية.
      if (!(error instanceof ApiError) || error.status !== 409) {
        const apiError = toApiError(error);
        return { error: apiError.detail ?? errors(apiError.key), message: null };
      }
    }
  }

  revalidatePath("/log");
  revalidatePath("/dashboard");
  return { error: null, message: t("saved") };
}
