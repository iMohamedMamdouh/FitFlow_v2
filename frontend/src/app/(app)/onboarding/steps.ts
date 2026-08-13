/**
 * خطوات الـ Onboarding وحالتها.
 *
 * منفصلة عن `actions.ts` لأن ملف `"use server"` لا يُصدِّر إلا دوالًا غير
 * متزامنة، والثوابت هنا تحتاجها الصفحة والنموذج معًا.
 */
export const STEPS = ["personal", "medical", "goals", "allergies"] as const;

export type Step = (typeof STEPS)[number];

export type StepState = { error: string | null; savedAt: number | null };

export const EMPTY_STEP_STATE: StepState = { error: null, savedAt: null };
