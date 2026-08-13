"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { ProfileRead } from "@/lib/api/schema";
import type { ConsentState } from "./state";

/**
 * تسجيل الموافقة على التنبيه الطبي (الخطوة 7.9).
 *
 * الموافقة فعل صريح لا مربّع مُعلَّم مسبقًا ولا استنتاج من متابعة
 * التسجيل: الخادم يرفض توليد أي خطة قبل وجود `consent_accepted_at`،
 * وهذه الشاشة هي المكان الوحيد الذي يضعه.
 */
export async function acceptConsentAction(
  _state: ConsentState,
  form: FormData,
): Promise<ConsentState> {
  const t = await getTranslations("consent");
  if (form.get("acknowledged") !== "on") return { error: t("mustCheck") };

  try {
    await apiFetch<ProfileRead>("/me/profile/consent", { method: "POST" });
  } catch (error) {
    const apiError = toApiError(error);
    const errors = await getTranslations("errors");
    return { error: apiError.detail ?? errors(apiError.key) };
  }

  revalidatePath("/", "layout");
  redirect("/dashboard");
}
