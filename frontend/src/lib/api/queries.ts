import "server-only";

import { cache } from "react";

import { apiFetch, apiFetchOrNull } from "./server";
import type {
  DailyLogRead,
  InjuryRead,
  InjuryTypeRead,
  PlanRead,
  PlanSummary,
  ProfileRead,
  ReadingRead,
  UserPublic,
} from "./schema";

/**
 * قراءات الخادم.
 *
 * كل دالة ملفوفة بـ `cache()` من React: الصفحة الواحدة قد تحتاج الملف
 * الشخصي في الرأسية وفي المحتوى معًا، وبدون التخزين المؤقت لطلب واحد
 * سيُنادى الـ API مرتين في نفس الـ render.
 */

export const getCurrentUser = cache(async (): Promise<UserPublic> => {
  return apiFetch<UserPublic>("/users/me");
});

/** يرجّع `null` لو لم يُستكمل الملف بعد — وهي حالة طبيعية لا خطأ. */
export const getProfile = cache(async (): Promise<ProfileRead | null> => {
  return apiFetchOrNull<ProfileRead>("/me/profile");
});

export const getReadings = cache(async (limit = 180): Promise<ReadingRead[]> => {
  return apiFetch<ReadingRead[]>(`/me/readings?limit=${limit}`);
});

export const getDailyLogs = cache(async (limit = 180): Promise<DailyLogRead[]> => {
  return apiFetch<DailyLogRead[]>(`/me/logs?limit=${limit}`);
});

export const getInjuries = cache(async (): Promise<InjuryRead[]> => {
  return apiFetch<InjuryRead[]>("/me/injuries");
});

export const getInjuryTypes = cache(async (): Promise<InjuryTypeRead[]> => {
  return apiFetch<InjuryTypeRead[]>("/catalog/injury-types");
});

/** الخطط المرئية للمريض فقط — الخادم يفلترها، لا الواجهة. */
export const getMyPlans = cache(async (): Promise<PlanSummary[]> => {
  return apiFetch<PlanSummary[]>("/me/plans");
});

export const getPlan = cache(async (planId: string): Promise<PlanRead | null> => {
  return apiFetchOrNull<PlanRead>(`/plans/${planId}`);
});

/** الخطة المفعّلة إن وُجدت، وإلا آخر خطة معتمدة. */
export const getActivePlan = cache(async (): Promise<PlanRead | null> => {
  const plans = await getMyPlans();
  const chosen = plans.find((plan) => plan.status === "active") ?? plans[0];
  if (chosen === undefined) return null;
  return getPlan(chosen.id);
});

/** أحدث قياس وزن مسجَّل — نفس تعريف الخادم لـ "الوزن الحالي". */
export function latestWeight(readings: readonly ReadingRead[]): string | null {
  for (const reading of readings) {
    if (reading.weight_kg !== null) return reading.weight_kg;
  }
  return null;
}

/** أقدم قياس وزن — نقطة البداية التي يُقاس عليها التغيّر. */
export function firstWeight(readings: readonly ReadingRead[]): string | null {
  for (let index = readings.length - 1; index >= 0; index -= 1) {
    const reading = readings[index];
    if (reading !== undefined && reading.weight_kg !== null) return reading.weight_kg;
  }
  return null;
}
