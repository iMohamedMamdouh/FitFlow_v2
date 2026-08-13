"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { SubmitButton } from "@/components/ui/submit-button";
import { generatePlanAction } from "@/lib/plans/actions";
import { EMPTY_PLAN_STATE } from "@/lib/plans/state";

export function GeneratePlanForm({ disabled }: { disabled: boolean }) {
  const t = useTranslations("plan");
  const dashboard = useTranslations("dashboard");
  const [state, formAction] = useActionState(generatePlanAction, EMPTY_PLAN_STATE);

  return (
    <form action={formAction} className="flex flex-col gap-3">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}
      <SubmitButton disabled={disabled} pendingLabel={dashboard("generating")}>
        {t("generate")}
      </SubmitButton>
    </form>
  );
}
