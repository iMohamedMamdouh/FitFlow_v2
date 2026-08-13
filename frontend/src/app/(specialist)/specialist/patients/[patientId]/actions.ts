"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { SpecialistNoteRead } from "@/lib/api/schema";
import type { NoteState } from "./state";

/**
 * إضافة ملاحظة على مريض (الخطوة 8.4).
 *
 * `is_internal` افتراضه غير مُعلَّم: الملاحظة تصل المريض ما لم يقل
 * الأخصائي غير ذلك. العكس — الخصوصية بالافتراض — يجعل رسالة موجّهة
 * للمريض تُكتب وتُحفظ ولا يراها أحد.
 */
export async function addNoteAction(
  patientId: string,
  _state: NoteState,
  form: FormData,
): Promise<NoteState> {
  const t = await getTranslations("specialist.notes");
  const raw = form.get("note");
  const note = typeof raw === "string" ? raw.trim() : "";

  if (note === "") return { error: t("placeholder"), message: null };

  try {
    await apiFetch<SpecialistNoteRead>(`/specialist/patients/${patientId}/notes`, {
      method: "POST",
      body: { note, is_internal: form.get("is_internal") === "on" },
    });
  } catch (error) {
    const apiError = toApiError(error);
    const errors = await getTranslations("errors");
    return { error: apiError.detail ?? errors(apiError.key), message: null };
  }

  revalidatePath(`/specialist/patients/${patientId}`);
  return { error: null, message: t("saved") };
}
