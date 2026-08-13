"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import { apiFetch } from "@/lib/api/server";
import type { AttachmentRead, InjuryRead } from "@/lib/api/schema";
import { MAX_UPLOAD_MB, type InjuryState } from "./state";

function text(form: FormData, key: string): string {
  const value = form.get(key);
  return typeof value === "string" ? value.trim() : "";
}

async function failure(error: unknown): Promise<InjuryState> {
  const apiError = toApiError(error);
  const t = await getTranslations("errors");
  return { error: apiError.detail ?? t(apiError.key), message: null };
}

/**
 * تسجيل إصابة (الخطوة 7.5).
 *
 * `injury_type_id` يأتي من قائمة `/catalog/injury-types` لا من نص حر:
 * نوع الإصابة يحدّد ما يُمنع من تمارين لاحقًا، ومعرّف مكتوب يدويًا يعني
 * إصابة مسجّلة على النوع الخطأ.
 */
export async function recordInjuryAction(
  _state: InjuryState,
  form: FormData,
): Promise<InjuryState> {
  const t = await getTranslations("injuries");
  const hadSurgery = form.get("had_surgery") === "on";
  const surgeryDate = text(form, "surgery_date");

  try {
    await apiFetch<InjuryRead>("/me/injuries", {
      method: "POST",
      body: {
        injury_type_id: text(form, "injury_type_id"),
        injury_date: text(form, "injury_date"),
        pain_level: Number(text(form, "pain_level")),
        status: text(form, "status"),
        side: text(form, "side"),
        had_surgery: hadSurgery,
        // تاريخ جراحة بلا جراحة يرفضه الخادم وقاعدة البيانات معًا — نرسل
        // الحقلين متسقين بدل انتظار رسالة الرفض.
        surgery_date: hadSurgery && surgeryDate !== "" ? surgeryDate : null,
        notes: text(form, "notes") || null,
      },
    });
  } catch (error) {
    return failure(error);
  }

  revalidatePath("/injuries");
  revalidatePath("/dashboard");
  return { error: null, message: t("saved") };
}

export async function uploadAttachmentAction(
  injuryId: string,
  _state: InjuryState,
  form: FormData,
): Promise<InjuryState> {
  const t = await getTranslations("injuries");
  const file = form.get("file");

  if (!(file instanceof File) || file.size === 0) {
    return { error: t("attachments.unsupported"), message: null };
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return { error: t("attachments.tooLarge", { limit: MAX_UPLOAD_MB }), message: null };
  }

  const payload = new FormData();
  payload.append("file", file);
  const fileType = text(form, "file_type");
  if (fileType !== "") payload.append("file_type", fileType);

  try {
    await apiFetch<AttachmentRead>(`/me/injuries/${injuryId}/attachments`, {
      method: "POST",
      formData: payload,
    });
  } catch (error) {
    return failure(error);
  }

  revalidatePath("/injuries");
  return { error: null, message: t("attachments.uploaded") };
}
