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
    <form action={formAction} className="mt-5 flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <label
            htmlFor={`file-${injuryId}`}
            className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase"
          >
            {t("file")}
          </label>
          <input
            id={`file-${injuryId}`}
            type="file"
            name="file"
            accept={ACCEPT}
            required
            className="border-line bg-raised text-ink file:bg-accent-wash file:text-accent hover:border-line-strong w-full rounded-lg border px-3.5 py-2.5 text-sm transition-colors file:me-3 file:rounded-md file:border-0 file:px-3 file:py-1.5 file:text-sm file:font-medium"
          />
          <p className="text-subtle text-xs leading-5">{t("hint", { limit: MAX_UPLOAD_MB })}</p>
        </div>

        <SelectField label={t("type")} name="file_type" defaultValue="photo">
          {FILE_TYPES.map((value) => (
            <option key={value} value={value}>
              {enums(value)}
            </option>
          ))}
        </SelectField>
      </div>

      <SubmitButton size="sm" variant="outline" pendingLabel={t("uploading")}>
        {t("upload")}
      </SubmitButton>
    </form>
  );
}
