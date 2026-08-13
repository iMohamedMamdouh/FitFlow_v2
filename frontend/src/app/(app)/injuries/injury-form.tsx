"use client";

import { useActionState, useState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { CheckboxField, SelectField, TextAreaField, TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { BODY_SIDES, INJURY_STATUSES, type InjuryTypeRead } from "@/lib/api/schema";
import { recordInjuryAction } from "./actions";
import { EMPTY_INJURY_STATE } from "./state";

export function InjuryForm({
  injuryTypes,
  today,
}: {
  injuryTypes: readonly InjuryTypeRead[];
  today: string;
}) {
  const t = useTranslations("injuries");
  const common = useTranslations("common");
  const enums = useTranslations("enums");
  const [state, formAction] = useActionState(recordInjuryAction, EMPTY_INJURY_STATE);

  // إظهار حقل تاريخ الجراحة مربوط بالمربّع: حقل ظاهر دائمًا يُملأ سهوًا
  // فيُرفض الطلب بقيد اتساق لا يفهمه المستخدم.
  const [hadSurgery, setHadSurgery] = useState(false);
  const [status, setStatus] = useState<string>("acute");

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <SelectField label={t("type")} name="injury_type_id" defaultValue="" required>
        <option value="" disabled>
          {t("typePlaceholder")}
        </option>
        {injuryTypes.map((injuryType) => (
          <option key={injuryType.id} value={injuryType.id}>
            {enums(`bodyRegion.${injuryType.body_region}`)} — {injuryType.name_ar}
            {injuryType.is_clinically_reviewed ? "" : ` (${common("notReviewed")})`}
          </option>
        ))}
      </SelectField>

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={t("date")}
          name="injury_date"
          type="date"
          max={today}
          defaultValue={today}
          required
        />
        <TextField
          label={t("pain")}
          name="pain_level"
          type="number"
          inputMode="numeric"
          min={0}
          max={10}
          step={1}
          defaultValue={5}
          required
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField
          label={t("status")}
          name="status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {INJURY_STATUSES.map((value) => (
            <option key={value} value={value}>
              {enums(`injuryStatus.${value}`)}
            </option>
          ))}
        </SelectField>
        <SelectField label={t("side")} name="side" defaultValue="not_applicable">
          {BODY_SIDES.map((value) => (
            <option key={value} value={value}>
              {enums(`bodySide.${value}`)}
            </option>
          ))}
        </SelectField>
      </div>

      {status === "acute" && <Alert tone="warning">{t("acuteWarning")}</Alert>}

      <CheckboxField
        label={t("hadSurgery")}
        name="had_surgery"
        checked={hadSurgery}
        onChange={(event) => setHadSurgery(event.target.checked)}
      />
      {hadSurgery && (
        <TextField label={t("surgeryDate")} name="surgery_date" type="date" max={today} required />
      )}

      <TextAreaField
        label={`${t("notes")} (${common("optional")})`}
        name="notes"
        maxLength={2000}
      />

      <SubmitButton pendingLabel={common("saving")}>{t("save")}</SubmitButton>
    </form>
  );
}
