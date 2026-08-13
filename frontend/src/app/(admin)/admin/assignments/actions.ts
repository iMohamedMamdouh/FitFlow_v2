"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import { capture, type AdminActionState } from "../users/state";

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

export async function assignPatientAction(
  specialistId: string,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.assignments");
  const patientId = String(form.get("patient_id") ?? "");
  if (patientId === "") {
    const errors = await getTranslations("errors");
    return {
      error: errors("validation"),
      message: null,
      values: capture(form),
      attempt: state.attempt + 1,
    };
  }

  try {
    await apiFetch("/admin/assignments", {
      method: "POST",
      body: { specialist_id: specialistId, patient_id: patientId },
    });
    refresh();
    return { error: null, message: t("assigned"), values: null, attempt: state.attempt + 1 };
  } catch (error) {
    return failure(error, state, form);
  }
}

export async function unassignPatientAction(
  specialistId: string,
  patientId: string,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.assignments");
  try {
    await apiFetch(`/admin/assignments/${specialistId}/${patientId}`, { method: "DELETE" });
    refresh();
    return { error: null, message: t("unassignDone"), values: null, attempt: state.attempt + 1 };
  } catch (error) {
    return failure(error, state, form);
  }
}
