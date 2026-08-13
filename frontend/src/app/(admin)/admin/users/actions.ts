"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";

import { toApiError } from "@/lib/api/errors";
import type { AdminUserRow, UserRole } from "@/lib/api/schema";
import { USER_ROLES } from "@/lib/api/schema";
import { apiFetch } from "@/lib/api/server";
import { capture, type AdminActionState } from "./state";

/**
 * أفعال المدير على الحسابات.
 *
 * الرسائل التي تصل من الخادم تُعرض كما هي: رفض تخفيض أخصائي له مرضى
 * يشرح **ما يجب فعله أولًا**، وترجمته إلى "حدث خطأ" يمحو ذلك.
 */

function refresh(): void {
  revalidatePath("/admin/users");
  revalidatePath("/admin/assignments");
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

function roleOf(form: FormData): UserRole | null {
  const value = form.get("role");
  return typeof value === "string" && (USER_ROLES as readonly string[]).includes(value)
    ? (value as UserRole)
    : null;
}

export async function setUserActiveAction(
  userId: string,
  isActive: boolean,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.users");
  try {
    await apiFetch<AdminUserRow>(`/admin/users/${userId}`, {
      method: "PATCH",
      body: { is_active: isActive },
    });
    refresh();
    return { error: null, message: t("saved"), values: null, attempt: state.attempt + 1 };
  } catch (error) {
    return failure(error, state, form);
  }
}

export async function setUserRoleAction(
  userId: string,
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.users");
  const role = roleOf(form);
  if (role === null) {
    const errors = await getTranslations("errors");
    return {
      error: errors("validation"),
      message: null,
      values: capture(form),
      attempt: state.attempt + 1,
    };
  }

  try {
    await apiFetch<AdminUserRow>(`/admin/users/${userId}`, {
      method: "PATCH",
      body: { role },
    });
    refresh();
    return { error: null, message: t("saved"), values: null, attempt: state.attempt + 1 };
  } catch (error) {
    return failure(error, state, form);
  }
}

export async function createStaffAction(
  state: AdminActionState,
  form: FormData,
): Promise<AdminActionState> {
  const t = await getTranslations("admin.users");
  const role = roleOf(form);
  if (role === null || role === "patient") {
    const errors = await getTranslations("errors");
    return {
      error: errors("validation"),
      message: null,
      values: capture(form),
      attempt: state.attempt + 1,
    };
  }

  try {
    await apiFetch("/admin/users", {
      method: "POST",
      body: {
        email: String(form.get("email") ?? "").trim(),
        password: String(form.get("password") ?? ""),
        full_name: String(form.get("full_name") ?? "").trim(),
        role,
      },
    });
    refresh();
    return { error: null, message: t("created"), values: null, attempt: state.attempt + 1 };
  } catch (error) {
    return failure(error, state, form);
  }
}
