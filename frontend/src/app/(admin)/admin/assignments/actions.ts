"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { AdminActionState } from "../users/state";

/**
 * إسناد المرضى وإنهاؤه.
 *
 * هذا هو الفعل الذي كان يُنفَّذ بـ `INSERT` يدوي حتى المرحلة العاشرة.
 * الفرق ليس الراحة: المسار يتحقق من الدورين، ويرفض الإسناد إلى أخصائي
 * معطَّل، ويكتب سطرًا في سجل التدقيق — وثلاثتها لا يفعلها SQL يدوي.
 */

function refresh(): void {
  revalidatePath("/admin/assignments");
  revalidatePath("/admin/users");
  revalidatePath("/admin");
}

async function failure(error: unknown): Promise<AdminActionState> {
  const apiError = toApiError(error);
  const t = await getTranslations("errors");
  return { error: apiError.detail ?? t(apiError.key), message: null };
}

export async function assignPatientAction(
  specialistId: string,
  _state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.assignments");
  const patientId = String(form.get("patient_id") ?? "");
  if (patientId === "") {
    const errors = await getTranslations("errors");
    return { error: errors("validation"), message: null };
  }

  try {
    await apiFetch("/admin/assignments", {
      method: "POST",
      body: { specialist_id: specialistId, patient_id: patientId },
    });
    refresh();
    return { error: null, message: t("assigned") };
  } catch (error) {
    return failure(error);
  }
}

export async function unassignPatientAction(
  specialistId: string,
  patientId: string,
  _state: AdminActionState,
  _form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.assignments");
  try {
    await apiFetch(`/admin/assignments/${specialistId}/${patientId}`, { method: "DELETE" });
    refresh();
    return { error: null, message: t("unassignDone") };
  } catch (error) {
    return failure(error);
  }
}
