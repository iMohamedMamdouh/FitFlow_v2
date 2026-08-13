"use client";

import { useActionState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/components/ui/nav-link";
import { Alert } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { CheckboxCard, SelectField, TextAreaField, TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { formatTime } from "@/lib/format";
import type { Locale } from "@/i18n/config";
import { ACTIVITY_LEVELS, ALLERGENS, GENDERS, GOALS } from "@/lib/api/schema";
import type { ProfileRead } from "@/lib/api/schema";
import { saveStepAction } from "./actions";
import { EMPTY_STEP_STATE, STEPS, type Step } from "./steps";

type Props = {
  step: Step;
  profile: ProfileRead | null;
  currentWeight: string | null;
};

export function OnboardingForm({ step, profile, currentWeight }: Props) {
  const t = useTranslations("onboarding");
  const enums = useTranslations("enums");
  const common = useTranslations("common");
  const locale = useLocale() as Locale;

  const [state, formAction] = useActionState(saveStepAction.bind(null, step), EMPTY_STEP_STATE);

  const index = STEPS.indexOf(step);
  const previous = STEPS[index - 1];
  const next = STEPS[index + 1];

  return (
    <form action={formAction} className="flex flex-col gap-5">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.savedAt !== null && (
        <Alert tone="success">
          {t("autosaved", { time: formatTime(locale, new Date(state.savedAt)) })}
        </Alert>
      )}

      {step === "personal" && (
        <>
          <TextField
            label={t("personal.birthDate")}
            hint={t("personal.birthDateHint")}
            name="birth_date"
            type="date"
            defaultValue={profile?.birth_date ?? ""}
            required
          />
          <SelectField
            label={t("personal.gender")}
            name="gender"
            defaultValue={profile?.gender ?? ""}
            required
          >
            <option value="" disabled />
            {GENDERS.map((value) => (
              <option key={value} value={value}>
                {enums(`gender.${value}`)}
              </option>
            ))}
          </SelectField>
          <TextField
            label={t("personal.heightCm")}
            name="height_cm"
            type="number"
            inputMode="decimal"
            min={50}
            max={260}
            step={0.1}
            defaultValue={profile?.height_cm ?? ""}
            required
          />
          <TextField
            label={t("personal.weightKg")}
            hint={t("personal.weightHint")}
            name="weight_kg"
            type="number"
            inputMode="decimal"
            min={20}
            max={500}
            step={0.1}
            defaultValue={currentWeight ?? ""}
            required
          />
        </>
      )}

      {step === "medical" && (
        <>
          <TextAreaField
            label={t("medical.history")}
            hint={t("medical.hint")}
            name="medical_history"
            placeholder={t("medical.historyPlaceholder")}
            defaultValue={asLines(profile?.medical_history)}
          />
          <TextAreaField
            label={t("medical.chronic")}
            name="chronic_diseases"
            placeholder={t("medical.chronicPlaceholder")}
            defaultValue={asLines(profile?.chronic_diseases)}
          />
          <TextAreaField
            label={t("medical.medications")}
            name="medications"
            placeholder={t("medical.medicationsPlaceholder")}
            defaultValue={asLines(profile?.medications)}
          />
          <TextAreaField
            label={`${t("medical.notes")} (${common("optional")})`}
            name="notes"
            defaultValue={profile?.notes ?? ""}
          />
        </>
      )}

      {step === "goals" && (
        <>
          <SelectField
            label={t("goals.goal")}
            hint={t("goals.hint")}
            name="goal"
            defaultValue={profile?.goal ?? ""}
            required
          >
            <option value="" disabled />
            {GOALS.map((value) => (
              <option key={value} value={value}>
                {enums(`goal.${value}`)}
              </option>
            ))}
          </SelectField>
          <SelectField
            label={t("goals.activity")}
            name="activity_level"
            defaultValue={profile?.activity_level ?? "sedentary"}
            required
          >
            {ACTIVITY_LEVELS.map((value) => (
              <option key={value} value={value}>
                {enums(`activityLevel.${value}`)}
              </option>
            ))}
          </SelectField>
        </>
      )}

      {step === "allergies" && (
        <>
          <Alert tone="warning">{t("allergies.warning")}</Alert>
          <fieldset className="grid gap-3 sm:grid-cols-2">
            <legend className="sr-only">{t("steps.allergies")}</legend>
            {ALLERGENS.map((value) => (
              <CheckboxCard
                key={value}
                label={enums(`allergen.${value}`)}
                name="allergens"
                value={value}
                defaultChecked={profile?.allergens?.includes(value) ?? false}
              />
            ))}
          </fieldset>
        </>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <input type="hidden" name="advance" value="1" />
        <SubmitButton pendingLabel={t("finishing")}>
          {next === undefined ? t("finish") : t(`steps.${next}`)}
        </SubmitButton>
        {previous !== undefined && (
          <Link
            href={`/onboarding?step=${previous}`}
            className={buttonStyles({ variant: "quiet" })}
          >
            {common("back")}
          </Link>
        )}
      </div>
    </form>
  );
}

function asLines(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value.map((entry) => String(entry)).join("\n");
}
