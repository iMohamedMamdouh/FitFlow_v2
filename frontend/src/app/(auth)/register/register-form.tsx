"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { registerAction } from "@/lib/auth/actions";
import { EMPTY_AUTH_STATE } from "@/lib/auth/state";

export function RegisterForm() {
  const t = useTranslations("auth");
  const [state, formAction] = useActionState(registerAction, EMPTY_AUTH_STATE);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}

      <TextField
        label={t("fullName")}
        name="full_name"
        autoComplete="name"
        required
        minLength={2}
      />
      <TextField
        label={t("email")}
        name="email"
        type="email"
        inputMode="email"
        autoComplete="email"
        dir="ltr"
        required
      />
      <TextField
        label={t("password")}
        name="password"
        type="password"
        autoComplete="new-password"
        dir="ltr"
        required
        minLength={12}
        hint={t("passwordHint")}
      />
      <SubmitButton block pendingLabel={t("registering")}>
        {t("register")}
      </SubmitButton>
    </form>
  );
}
