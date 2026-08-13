import { getTranslations } from "next-intl/server";

import { Link } from "@/components/ui/nav-link";
import { Alert } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import type { ProfileRead } from "@/lib/api/schema";

/**
 * تنبيه ما ينقص قبل أن يعمل النظام.
 *
 * الخادم يرفض توليد أي خطة قبل استكمال الملف والموافقة على التنبيه
 * الطبي. عرض هذا الشرط كخطوة ناقصة أفضل من تركه يظهر كرسالة خطأ بعد أن
 * يضغط المستخدم زر التوليد.
 */
export async function SetupGate({ profile }: { profile: ProfileRead | null }) {
  const consent = await getTranslations("consent");
  const profileText = await getTranslations("profile");

  if (profile === null) {
    return (
      <Alert tone="warning">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span>{profileText("incomplete")}</span>
          <Link href="/onboarding" className={buttonStyles({ size: "sm" })}>
            {profileText("complete")}
          </Link>
        </div>
      </Alert>
    );
  }

  if (profile.consent_accepted_at === null) {
    return (
      <Alert tone="warning">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span>{consent("required")}</span>
          <Link href="/consent" className={buttonStyles({ size: "sm" })}>
            {consent("goToConsent")}
          </Link>
        </div>
      </Alert>
    );
  }

  return null;
}

/** هل النظام جاهز لتوليد خطة لهذا المستخدم؟ */
export function isReadyForPlan(profile: ProfileRead | null): boolean {
  return profile !== null && profile.consent_accepted_at !== null;
}
