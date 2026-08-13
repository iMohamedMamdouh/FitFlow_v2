import { getTranslations } from "next-intl/server";

import { Alert } from "@/components/ui/alert";

/**
 * التنبيه الطبي المختصر (الخطوة 7.9).
 *
 * يظهر في كل شاشة تعرض خطة أو رقمًا غذائيًا. تكراره مقصود: تنبيه يُقرأ
 * مرة عند التسجيل ثم يختفي لا يؤدي وظيفته وقت اتخاذ القرار.
 */
export async function MedicalDisclaimer({ className }: { className?: string }) {
  const t = await getTranslations("consent");
  return (
    <Alert tone="warning" className={className}>
      {t("shortNotice")}
    </Alert>
  );
}
