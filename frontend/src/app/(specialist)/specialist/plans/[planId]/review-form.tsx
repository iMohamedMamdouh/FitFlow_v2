"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { TextAreaField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import type { PlanStatus } from "@/lib/api/schema";
import { activatePlanAction, approvePlanAction, requestChangesAction } from "./actions";
import { EMPTY_REVIEW_STATE } from "./state";

/**
 * شاشة القرار.
 *
 * الأفعال المتاحة تُشتق من حالة الخطة لا تُعرض كلها معطّلة: زر "تفعيل"
 * على خطة قيد المراجعة لا معنى له، ووجوده يدعو للضغط ثم يردّ بخطأ.
 *
 * رسائل النتيجة تُعرض **قبل** أي تفرّع على الحالة. القرار الناجح يغيّر
 * الحالة، فلو كانت الرسالة داخل فرع "قيد المراجعة" لاختفت في اللحظة
 * نفسها التي يُفترض أن تؤكّد فيها ما حدث.
 */
export function ReviewForm({ planId, status }: { planId: string; status: PlanStatus }) {
  const t = useTranslations("specialist.plan");

  const approved = status === "approved";
  const pendingReview = status === "pending_review";

  const [decision, decide] = useActionState(
    approved ? activatePlanAction.bind(null, planId) : approvePlanAction.bind(null, planId),
    EMPTY_REVIEW_STATE,
  );
  const [changes, requestChanges] = useActionState(
    requestChangesAction.bind(null, planId),
    EMPTY_REVIEW_STATE,
  );

  const error = decision.error ?? changes.error;
  const message = decision.message ?? changes.message;

  return (
    <div className="flex flex-col gap-5">
      {error !== null && <Alert tone="danger">{error}</Alert>}
      {message !== null && <Alert tone="success">{message}</Alert>}

      {approved && (
        <form action={decide}>
          <SubmitButton variant="clay" pendingLabel={t("activating")}>
            {t("activate")}
          </SubmitButton>
        </form>
      )}

      {pendingReview && (
        // حقل سبب واحد يقرأه الفعلان: اختياري مع الاعتماد وإلزامي مع طلب
        // التعديل، وحقلان منفصلان يعنيان كتابته مرتين.
        <form action={decide} className="flex flex-col gap-4">
          <TextAreaField
            label={t("reason")}
            hint={t("reasonHint")}
            name="reason"
            maxLength={2000}
            rows={4}
          />
          <div className="flex flex-wrap gap-3">
            <SubmitButton pendingLabel={t("approving")}>{t("approve")}</SubmitButton>
            <SubmitButton
              variant="outline"
              formAction={requestChanges}
              pendingLabel={t("requesting")}
            >
              {t("requestChanges")}
            </SubmitButton>
          </div>
        </form>
      )}

      {!approved && !pendingReview && <Alert tone="info">{t("noActions")}</Alert>}
    </div>
  );
}
