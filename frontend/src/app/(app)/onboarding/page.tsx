import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Card, CardHeader } from "@/components/ui/card";
import { getProfile, getReadings, latestWeight } from "@/lib/api/queries";
import { cn } from "@/lib/utils";
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
    <div className="mx-auto flex max-w-xl flex-col gap-7">
      <header className="flex flex-col gap-1.5">
        <span className="text-faint text-[0.7rem] font-semibold tracking-[0.14em] uppercase">
          {t("stepLabel", { current: index + 1, total: STEPS.length })}
        </span>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      {/* شريط تقدّم بأربع قطع: يوضّح الموقع في الرحلة بلا نسبة مئوية
          مصطنعة، ويبقى مقروءًا في أضيق شاشة. */}
      <ol className="flex gap-2" aria-label={t("title")}>
        {STEPS.map((name, position) => (
          <li
            key={name}
            aria-current={position === index ? "step" : undefined}
            className="flex flex-1 flex-col gap-1.5"
          >
            <span
              className={cn(
                "h-1 rounded-full transition-colors",
                position < index && "bg-accent",
                position === index && "bg-clay",
                position > index && "bg-line",
              )}
            />
            <span
              className={cn(
                "hidden text-[0.7rem] sm:block",
                position === index ? "text-ink font-medium" : "text-faint",
              )}
            >
              {t(`steps.${name}`)}
            </span>
          </li>
        ))}
      </ol>

      <Card>
        <CardHeader title={t(`steps.${step}`)} description={t(`${step}.hint`)} />
        <OnboardingForm step={step} profile={profile} currentWeight={latestWeight(readings)} />
      </Card>
    </div>
  );
}
