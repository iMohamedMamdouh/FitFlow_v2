import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Alert } from "@/components/ui/alert";
import { Card, CardHeader } from "@/components/ui/card";
import { getProfile } from "@/lib/api/queries";
import { formatDateTime } from "@/lib/format";
import { ConsentForm } from "./consent-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("consent");
  return { title: t("title") };
}

export default async function ConsentPage() {
  const t = await getTranslations("consent");
  const profile = await getProfile();

  // لا موافقة بلا ملف: الخادم يرفض تسجيلها، فالتوجيه هنا يمنع رسالة خطأ.
  if (profile === null) redirect("/onboarding");

  const points = [t("point1"), t("point2"), t("point3"), t("point4"), t("point5")];

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5">
      <Card>
        <CardHeader title={t("title")} description={t("lead")} />

        <ul className="flex list-disc flex-col gap-3 ps-5 text-sm leading-7">
          {points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>

        <Alert tone="danger" className="mt-5">
          {t("emergency")}
        </Alert>
      </Card>

      <Card>
        {profile.consent_accepted_at !== null ? (
          <Alert tone="success">
            {t("acceptedAt", { date: formatDateTime(profile.consent_accepted_at) })}
          </Alert>
        ) : (
          <ConsentForm />
        )}
      </Card>
    </div>
  );
}
