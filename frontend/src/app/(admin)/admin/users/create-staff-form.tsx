"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { SelectField, TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { createStaffAction } from "./actions";
import { EMPTY_ADMIN_STATE } from "./state";

/**
 * إنشاء حساب أخصائي أو مدير.
 *
 * المريض ليس ضمن الخيارات: له تسجيل عام، وإدراجه هنا يفتح طريقًا ثانيًا
 * لإنشاء حسابات المرضى بلا موافقة ولا onboarding.
 */
export function CreateStaffForm() {
  const t = useTranslations("admin.users");
  const auth = useTranslations("auth");
  const roles = useTranslations("roles");
  const [state, submit] = useActionState(createStaffAction, EMPTY_ADMIN_STATE);

  return (
    <form action={submit} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label={auth("fullName")} name="full_name" required minLength={2} />
        <TextField label={auth("email")} name="email" type="email" required />
        <TextField
          label={auth("password")}
          name="password"
          type="password"
          hint={auth("passwordHint")}
          required
          minLength={12}
        />
        <SelectField label={t("roleFilter")} name="role" defaultValue="specialist">
          <option value="specialist">{roles("specialist")}</option>
          <option value="admin">{roles("admin")}</option>
        </SelectField>
      </div>

      <div>
        <SubmitButton pendingLabel={t("creating")}>{t("create")}</SubmitButton>
      </div>
    </form>
  );
}
