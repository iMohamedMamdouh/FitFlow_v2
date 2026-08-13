"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert, Badge } from "@/components/ui/alert";
import { SubmitButton } from "@/components/ui/submit-button";
import type { AdminUserRow } from "@/lib/api/schema";
import { USER_ROLES } from "@/lib/api/schema";
import { setUserActiveAction, setUserRoleAction } from "./actions";
import { EMPTY_ADMIN_STATE } from "./state";

/**
 * سطر مستخدم مع أفعاله.
 *
 * كل سطر يحمل حالته: رفض تخفيض أخصائي له مرضى يخصّ **هذا** الأخصائي،
 * وعرضه في تنبيه أعلى الصفحة يترك القارئ يبحث عن صاحب الرسالة.
 *
 * حساب المدير نفسه يظهر بلا أفعال: الخادم يرفضها (وهو الحكم)، وإظهار
 * أزرار لا تعمل دعوة إلى الضغط ثم قراءة خطأ.
 */
export function UserRow({ user, isSelf }: { user: AdminUserRow; isSelf: boolean }) {
  const t = useTranslations("admin.users");
  const roles = useTranslations("roles");

  const [statusState, toggleStatus] = useActionState(
    setUserActiveAction.bind(null, user.id, !user.is_active),
    EMPTY_ADMIN_STATE,
  );
  const [roleState, changeRole] = useActionState(
    setUserRoleAction.bind(null, user.id),
    EMPTY_ADMIN_STATE,
  );

  const error = statusState.error ?? roleState.error;
  const message = statusState.message ?? roleState.message;

  return (
    <div className="border-line bg-surface flex flex-col gap-4 rounded-xs border p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display font-semibold tracking-tight">
            {user.full_name}
            {isSelf && <span className="text-faint ms-2 text-xs font-normal">{t("self")}</span>}
          </p>
          <p className="text-subtle mt-1 text-xs break-all">{user.email}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Badge tone={user.role === "patient" ? "neutral" : "accent"}>{roles(user.role)}</Badge>
          {!user.is_active && <Badge tone="danger">{t("disabled")}</Badge>}
        </div>
      </div>

      <p className="text-subtle text-xs leading-6">
        {user.role === "specialist" && t("assignedPatients", { count: user.assigned_patients })}
        {user.role === "patient" &&
          (user.specialists.length > 0
            ? t("specialists", {
                names: user.specialists.map((entry) => entry.full_name).join("، "),
              })
            : t("noSpecialist"))}
      </p>

      {error !== null && <Alert tone="danger">{error}</Alert>}
      {message !== null && <Alert tone="success">{message}</Alert>}

      {!isSelf && (
        <div className="flex flex-wrap items-end gap-3">
          <form action={changeRole} className="flex items-end gap-2">
            <label className="flex flex-col gap-1.5">
              <span className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
                {t("changeRole")}
              </span>
              <select
                name="role"
                defaultValue={user.role}
                className="border-line border-b-line-strong bg-raised text-ink rounded-xs border border-b-2 px-3 py-2 text-sm"
              >
                {USER_ROLES.map((role) => (
                  <option key={role} value={role}>
                    {roles(role)}
                  </option>
                ))}
              </select>
            </label>
            <SubmitButton variant="outline" size="sm" pendingLabel={t("saving")}>
              {t("save")}
            </SubmitButton>
          </form>

          <form action={toggleStatus}>
            <SubmitButton
              variant={user.is_active ? "quiet" : "signal"}
              size="sm"
              pendingLabel={t("saving")}
            >
              {user.is_active ? t("deactivate") : t("activate")}
            </SubmitButton>
          </form>
        </div>
      )}
    </div>
  );
}
