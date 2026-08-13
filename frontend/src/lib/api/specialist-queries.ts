import "server-only";

import { cache } from "react";

import { apiFetch, apiFetchOrNull } from "./server";
import type {
  AuditEntryRead,
  DailyLogRead,
  InjuryRead,
  InjuryTypeRead,
  PatientSummary,
  PlanRead,
  PlanSummary,
  PlanTransitionRead,
  ProfileRead,
  ReadingRead,
  SpecialistNoteRead,
  UserPublic,
} from "./schema";

/**
 * قراءات لوحة الأخصائي.
 *
 * كلها ملفوفة بـ `cache()`: صفحة ملف المريض تحتاج ملخّصه في الرأسية
 * وتفاصيله في المحتوى، وبدون التخزين المؤقت لطلب واحد يتكرر النداء.
 */

export const getMyPatients = cache(async (): Promise<PatientSummary[]> => {
  return apiFetch<PatientSummary[]>("/specialist/patients");
});

export const getReviewQueue = cache(async (): Promise<PlanSummary[]> => {
  return apiFetch<PlanSummary[]>("/specialist/review-queue");
});

/**
 * ملخّص مريض بعينه — من القائمة لا من مسار منفصل.
 *
 * القائمة **هي** مصدر المؤشرات، ولا يوجد مسار يرجّع ملخّص مريض واحد.
 * اشتقاقه هنا يضمن أن ما يظهر في الملف مطابق لما يظهر في القائمة، ويمنع
 * أن يصبح الحساب نسختين تتباعدان.
 */
export const getPatientSummary = cache(
  async (patientId: string): Promise<PatientSummary | null> => {
    const patients = await getMyPatients();
    return patients.find((patient) => patient.id === patientId) ?? null;
  },
);

/** يرجّع `null` لو لم يستكمل المريض ملفه — حالة طبيعية لا خطأ. */
export const getPatientProfile = cache(async (patientId: string): Promise<ProfileRead | null> => {
  return apiFetchOrNull<ProfileRead>(`/specialist/patients/${patientId}/profile`);
});

export const getPatientInjuries = cache(async (patientId: string): Promise<InjuryRead[]> => {
  return apiFetch<InjuryRead[]>(`/specialist/patients/${patientId}/injuries`);
});

export const getPatientReadings = cache(
  async (patientId: string, limit = 180): Promise<ReadingRead[]> => {
    return apiFetch<ReadingRead[]>(`/specialist/patients/${patientId}/readings?limit=${limit}`);
  },
);

export const getPatientLogs = cache(
  async (patientId: string, limit = 180): Promise<DailyLogRead[]> => {
    return apiFetch<DailyLogRead[]>(`/specialist/patients/${patientId}/logs?limit=${limit}`);
  },
);

export const getPatientPlans = cache(async (patientId: string): Promise<PlanSummary[]> => {
  return apiFetch<PlanSummary[]>(`/specialist/patients/${patientId}/plans`);
});

export const getPatientNotes = cache(async (patientId: string): Promise<SpecialistNoteRead[]> => {
  return apiFetch<SpecialistNoteRead[]>(`/specialist/patients/${patientId}/notes`);
});

export const getPatientAudit = cache(async (patientId: string): Promise<AuditEntryRead[]> => {
  return apiFetch<AuditEntryRead[]>(`/specialist/patients/${patientId}/audit`);
});

export const getPlanForReview = cache(async (planId: string): Promise<PlanRead | null> => {
  return apiFetchOrNull<PlanRead>(`/plans/${planId}`);
});

export const getPlanHistory = cache(async (planId: string): Promise<PlanTransitionRead[]> => {
  return apiFetch<PlanTransitionRead[]>(`/plans/${planId}/history`);
});

export const getStaff = cache(async (): Promise<UserPublic[]> => {
  return apiFetch<UserPublic[]>("/admin/users");
});

export const getInjuryTypes = cache(async (): Promise<InjuryTypeRead[]> => {
  return apiFetch<InjuryTypeRead[]>("/catalog/injury-types");
});
