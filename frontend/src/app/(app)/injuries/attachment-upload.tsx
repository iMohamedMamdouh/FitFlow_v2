"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { SelectField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import { uploadAttachmentAction } from "./actions";
import { EMPTY_INJURY_STATE, MAX_UPLOAD_MB } from "./state";

const FILE_TYPES = ["xray", "mri", "ct_scan", "ultrasound", "report", "photo", "other"] as const;

/** أنواع مقبولة على الخادم — نضعها في `accept` لتصفية أولية في المتصفح. */
const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";

export function AttachmentUpload({ injuryId }: { injuryId: string }) {
  const t = useTranslations("injuries.attachments");
  const enums = useTranslations("enums.attachmentType");
  const [state, formAction] = useActionState(
    uploadAttachmentAction.bind(null, injuryId),
    EMPTY_INJURY_STATE,
  );

  return (
    <form action={formAction} className="mt-4 flex flex-col gap-3">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={`file-${injuryId}`} className="text-sm font-medium">
            {t("upload")}
          </label>
          <input
            id={`file-${injuryId}`}
            type="file"
            name="file"
            accept={ACCEPT}
            required
            className="border-border bg-surface file:bg-muted-surface file:text-foreground w-full rounded-lg border px-3 py-2 text-sm file:me-3 file:rounded-md file:border-0 file:px-3 file:py-1.5 file:text-sm"
          />
          <p className="text-muted text-xs leading-5">{t("hint", { limit: MAX_UPLOAD_MB })}</p>
        </div>

        <SelectField label={enums("photo")} name="file_type" defaultValue="photo">
          {FILE_TYPES.map((value) => (
            <option key={value} value={value}>
              {enums(value)}
            </option>
          ))}
        </SelectField>
      </div>

      <SubmitButton size="sm" pendingLabel={t("uploading")}>
        {t("upload")}
      </SubmitButton>
    </form>
  );
}
