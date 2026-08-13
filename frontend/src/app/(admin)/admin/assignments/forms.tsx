"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { SubmitButton } from "@/components/ui/submit-button";
import type { AdminUserRow } from "@/lib/api/schema";
import { EMPTY_ADMIN_STATE } from "../users/state";
import { assignPatientAction, unassignPatientAction } from "./actions";

/**
 * نموذج الإسناد.
 *
 * قائمة المرضى المعروضة هنا **غير المسنَدين لهذا الأخصائي** فقط: عرض
 * الكل يجعل الخيار الأكثر احتمالًا للخطأ (مريض مسنَد أصلًا) هو الأقرب
 * للاختيار، ويردّ الخادم بـ 409 على فعل كان يمكن ألا يُعرض أصلًا.
 */
export function AssignForm({
  specialistId,
  candidates,
}: {
  specialistId: string;
  candidates: readonly AdminUserRow[];
}) {
  const t = useTranslations("admin.assignments");
  const [state, submit] = useActionState(
    assignPatientAction.bind(null, specialistId),
    EMPTY_ADMIN_STATE,
  );

  return (
    <form action={submit} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="flex flex-wrap items-end gap-3">
        <label className="flex min-w-56 flex-1 flex-col gap-1.5">
          <span className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
            {t("patient")}
          </span>
          <select
            name="patient_id"
            defaultValue=""
            required
            disabled={candidates.length === 0}
            className="border-line border-b-line-strong bg-raised text-ink rounded-xs border border-b-2 px-3.5 py-2.5 text-sm disabled:opacity-60"
          >
            <option value="" disabled>
              {t("pickPatient")}
            </option>
            {candidates.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.full_name} — {patient.email}
              </option>
            ))}
          </select>
        </label>
        <SubmitButton
          variant="signal"
          pendingLabel={t("assigning")}
          disabled={candidates.length === 0}
        >
          {t("assign")}
        </SubmitButton>
      </div>
    </form>
  );
}

export function UnassignButton({
  specialistId,
  patientId,
}: {
  specialistId: string;
  patientId: string;
}) {
  const t = useTranslations("admin.assignments");
  const [state, submit] = useActionState(
    unassignPatientAction.bind(null, specialistId, patientId),
    EMPTY_ADMIN_STATE,
  );

  return (
    <form action={submit} className="flex flex-col items-end gap-2">
      <SubmitButton variant="outline" size="sm" pendingLabel={t("unassigning")}>
        {t("unassign")}
      </SubmitButton>
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
    </form>
  );
}
