"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { CheckboxField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { acceptConsentAction } from "./actions";
import { EMPTY_CONSENT_STATE } from "./state";

export function ConsentForm() {
  const t = useTranslations("consent");
  const [state, formAction] = useActionState(acceptConsentAction, EMPTY_CONSENT_STATE);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      <CheckboxField label={t("checkbox")} name="acknowledged" />
      <SubmitButton pendingLabel={t("accepting")}>{t("accept")}</SubmitButton>
    </form>
  );
}
