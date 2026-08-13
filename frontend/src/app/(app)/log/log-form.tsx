"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { TextAreaField, TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { saveDailyLogAction } from "./actions";
import { EMPTY_LOG_STATE } from "./state";

export function LogForm({ today, currentWeight }: { today: string; currentWeight: string | null }) {
  const t = useTranslations("log");
  const common = useTranslations("common");
  const [state, formAction] = useActionState(saveDailyLogAction, EMPTY_LOG_STATE);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <TextField
        label={t("date")}
        name="log_date"
        type="date"
        defaultValue={today}
        max={today}
        required
      />
      <TextField
        label={t("weight")}
        name="weight_kg"
        type="number"
        inputMode="decimal"
        min={20}
        max={500}
        step={0.1}
        defaultValue={currentWeight ?? ""}
      />
      <TextField
        label={t("pain")}
        hint={t("painScale")}
        name="pain_level"
        type="number"
        inputMode="numeric"
        min={0}
        max={10}
        step={1}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={t("dietAdherence")}
          name="diet_adherence_pct"
          type="number"
          inputMode="numeric"
          min={0}
          max={100}
          step={5}
        />
        <TextField
          label={t("exerciseAdherence")}
          name="exercise_adherence_pct"
          type="number"
          inputMode="numeric"
          min={0}
          max={100}
          step={5}
        />
      </div>
      <TextAreaField
        label={`${t("notes")} (${common("optional")})`}
        name="notes"
        maxLength={1000}
      />

      <SubmitButton pendingLabel={common("saving")}>{t("save")}</SubmitButton>
    </form>
  );
}
