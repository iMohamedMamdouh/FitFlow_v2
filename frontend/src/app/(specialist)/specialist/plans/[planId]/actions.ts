"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { PlanRead } from "@/lib/api/schema";
import type { ReviewState } from "./state";

/**
 * قرار الأخصائي على خطة (الخطوة 8.3).
 *
 * الثلاثة أفعال منفصلة لا فعل واحد بمعامل: الاعتماد وطلب التعديل
 * والتفعيل انتقالات مختلفة في آلة الحالات، ولكلٍّ منها شرط مختلف —
 * ودمجها في مسار واحد يجعل خطأ في قيمة واحدة كافيًا لتفعيل خطة كان
 * المفروض ردّها.
 *
 * التحقق النهائي ليس هنا ولا في الخادم وحده: قاعدة البيانات ترفض أي
 * انتقال غير مسموح بـ trigger (ADR-006). ما هنا رسائل مفهومة لا حاجز.
 */

function reasonOf(form: FormData): string {
  const value = form.get("reason");
  return typeof value === "string" ? value.trim() : "";
}

async function failure(error: unknown): Promise<ReviewState> {
  const apiError = toApiError(error);
  const t = await getTranslations("errors");
  return { error: apiError.detail ?? t(apiError.key), message: null };
}

function refresh(planId: string): void {
  revalidatePath(`/specialist/plans/${planId}`);
  revalidatePath("/specialist/review");
  revalidatePath("/specialist");
}

export async function approvePlanAction(
  planId: string,
  _state: ReviewState,
  form: FormData,
): Promise<ReviewState> {
  const t = await getTranslations("specialist.plan");
  try {
    await apiFetch<PlanRead>(`/plans/${planId}/approve`, {
      method: "POST",
      body: { reason: reasonOf(form) || null },
    });
  } catch (error) {
    return failure(error);
  }
  refresh(planId);
  return { error: null, message: t("approved") };
}

export async function requestChangesAction(
  planId: string,
  _state: ReviewState,
  form: FormData,
): Promise<ReviewState> {
  const t = await getTranslations("specialist.plan");
  const reason = reasonOf(form);

  // الرفض بلا سبب يترك المريض بخطة مردودة لا يعرف ما فيها — والسبب هو
  // كل ما يصله من هذا القرار.
  if (reason.length < 3) return { error: t("reasonRequired"), message: null };

  try {
    await apiFetch<PlanRead>(`/plans/${planId}/request-changes`, {
      method: "POST",
      body: { reason },
    });
  } catch (error) {
    return failure(error);
  }
  refresh(planId);
  return { error: null, message: t("changesRequested") };
}

export async function activatePlanAction(
  planId: string,
  _state: ReviewState,
  _form: FormData,
): Promise<ReviewState> {
  const t = await getTranslations("specialist.plan");
  try {
    await apiFetch<PlanRead>(`/plans/${planId}/activate`, { method: "POST" });
  } catch (error) {
    return failure(error);
  }
  refresh(planId);
  return { error: null, message: t("activated") };
}
