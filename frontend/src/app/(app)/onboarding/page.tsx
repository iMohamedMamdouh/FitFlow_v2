import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Card, CardHeader } from "@/components/ui/card";
import { getProfile, getReadings, latestWeight } from "@/lib/api/queries";
import { STEPS, type Step } from "./steps";
import { OnboardingForm } from "./onboarding-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("onboarding");
  return { title: t("title") };
}

function parseStep(value: string | undefined): Step {
  return (STEPS as readonly string[]).includes(value ?? "") ? (value as Step) : STEPS[0];
}

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<{ step?: string }>;
}) {
  const t = await getTranslations("onboarding");
  const { step: requested } = await searchParams;
  const step = parseStep(requested);

  const [profile, readings] = await Promise.all([getProfile(), getReadings(1)]);

  // الملف مكتمل والموافقة مسجَّلة: لا معنى لإعادة عرض التهيئة.
  if (requested === undefined && profile !== null && profile.consent_accepted_at !== null) {
    redirect("/dashboard");
  }

  const index = STEPS.indexOf(step);

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-5">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-bold">{t("title")}</h1>
        <p className="text-muted text-sm leading-7">{t("subtitle")}</p>
      </header>

      <ol className="flex flex-wrap gap-2 text-xs" aria-label={t("title")}>
        {STEPS.map((name, position) => (
          <li
            key={name}
            aria-current={position === index ? "step" : undefined}
            className={
              position === index
                ? "bg-primary text-primary-foreground rounded-full px-3 py-1 font-medium"
                : position < index
                  ? "bg-primary-soft text-primary-strong rounded-full px-3 py-1"
                  : "bg-muted-surface text-muted rounded-full px-3 py-1"
            }
          >
            {t(`steps.${name}`)}
          </li>
        ))}
      </ol>

      <Card>
        <CardHeader
          title={t(`steps.${step}`)}
          description={t("stepLabel", { current: index + 1, total: STEPS.length })}
        />
        <OnboardingForm step={step} profile={profile} currentWeight={latestWeight(readings)} />
      </Card>
    </div>
  );
}
