"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { PlanRead } from "@/lib/api/schema";
import type { PlanActionState } from "./state";

async function failure(error: unknown): Promise<PlanActionState> {
  const apiError = toApiError(error);
  const t = await getTranslations("errors");
  return { error: apiError.detail ?? t(apiError.key), message: null };
}

/**
 * توليد خطة (الخطوة 7.6).
 *
 * الخطة تعود **مسودة** دائمًا ولا تظهر للمريض. هذا ليس تفصيلًا في
 * الواجهة بل قرار معماري (ADR-006) مفروض في قاعدة البيانات نفسها، لذلك
 * الرسالة تقول صراحةً إن ما تولّد ذهب للمراجعة لا إليه.
 */
export async function generatePlanAction(
  _state: PlanActionState,
  _form: FormData,
): Promise<PlanActionState> {
  const t = await getTranslations("plan");
  let plan: PlanRead;
  try {
    plan = await apiFetch<PlanRead>("/plans/generate", {
      method: "POST",
      body: { plan_type: "nutrition" },
    });
  } catch (error) {
    return failure(error);
  }

  // الخطة المولَّدة مسودة يملكها المريض، فيمكنه إرسالها للمراجعة فورًا.
  try {
    await apiFetch<PlanRead>(`/plans/${plan.id}/submit`, { method: "POST" });
  } catch (error) {
    return failure(error);
  }

  revalidatePath("/plan");
  revalidatePath("/dashboard");
  return { error: null, message: `${t("generated")} ${t("sentForReview")}` };
}
