import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { getMyPatients, getReviewQueue } from "@/lib/api/specialist-queries";
import { formatDate } from "@/lib/format";
import { readLocale } from "@/lib/preferences";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("specialist.review");
  return { title: t("title") };
}

export default async function ReviewQueuePage() {
  const t = await getTranslations("specialist.review");
  const enums = await getTranslations("enums");
  const common = await getTranslations("common");
  const locale = await readLocale();

  const [queue, patients] = await Promise.all([getReviewQueue(), getMyPatients()]);
  const nameOf = new Map(patients.map((patient) => [patient.id, patient.full_name]));

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      {queue.length === 0 ? (
        <Card>
          <CardHeader title={t("empty")} description={t("emptyHint")} />
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {/* الأقدم أولًا: الترتيب يأتي من الخادم، فالخطة التي انتظرت أطول
              تظهر أعلى بدل أن تُدفن تحت الأحدث. */}
          {queue.map((plan) => (
            <Card key={plan.id} className="flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0">
                <h2 className="font-display truncate font-semibold tracking-tight">
                  {nameOf.get(plan.user_id) ?? common("unknown")}
                </h2>
                <p className="text-subtle mt-1 text-sm tabular-nums">
                  {t("submittedAt", { date: formatDate(locale, plan.created_at) })}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Badge tone="clay">{enums(`planType.${plan.plan_type}`)}</Badge>
                <Link
                  href={`/specialist/plans/${plan.id}`}
                  className={buttonStyles({ variant: "clay", size: "sm" })}
                >
                  {t("open")}
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
