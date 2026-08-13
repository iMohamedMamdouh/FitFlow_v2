"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { loginAction } from "@/lib/auth/actions";
import { EMPTY_AUTH_STATE } from "@/lib/auth/state";

export function LoginForm({ next }: { next: string | null }) {
  const t = useTranslations("auth");
  const [state, formAction] = useActionState(loginAction, EMPTY_AUTH_STATE);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {next !== null && <input type="hidden" name="next" value={next} />}
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}

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
        autoComplete="current-password"
        dir="ltr"
        required
      />
      <SubmitButton block pendingLabel={t("loggingIn")}>
        {t("login")}
      </SubmitButton>
    </form>
  );
}
