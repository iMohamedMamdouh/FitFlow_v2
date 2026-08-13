"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { CheckboxField, TextAreaField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { addNoteAction } from "./actions";
import { EMPTY_NOTE_STATE } from "./state";

export function NoteForm({ patientId }: { patientId: string }) {
  const t = useTranslations("specialist.notes");
  const [state, formAction] = useActionState(addNoteAction.bind(null, patientId), EMPTY_NOTE_STATE);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <TextAreaField
        label={t("add")}
        name="note"
        placeholder={t("placeholder")}
        maxLength={4000}
        rows={3}
        required
      />
      <CheckboxField label={t("internal")} name="is_internal" />
      <SubmitButton size="sm" pendingLabel={t("save")}>
        {t("save")}
      </SubmitButton>
    </form>
  );
}
