import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { SetupGate } from "@/components/setup-gate";
import { Alert } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { getCurrentUser, getProfile, getReadings, latestWeight } from "@/lib/api/queries";
import { bodyMassIndex, formatDateTime, formatNumber } from "@/lib/format";
import { readLocale } from "@/lib/preferences";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("profile");
  return { title: t("title") };
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">{label}</dt>
      <dd className="mt-1.5 text-sm leading-7">{value}</dd>
    </div>
  );
}

export default async function ProfilePage() {
  const t = await getTranslations("profile");
  const enums = await getTranslations("enums");
  const consent = await getTranslations("consent");
  const dashboard = await getTranslations("dashboard");
  const locale = await readLocale();

  const [user, profile, readings] = await Promise.all([
    getCurrentUser(),
    getProfile(),
    getReadings(1),
  ]);

  if (profile === null) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <SetupGate profile={null} />
      </div>
    );
  }

  const weight = latestWeight(readings);
  const bmi = bodyMassIndex(weight, profile.height_cm);
  // `allergens` اختياري في المخطط المولَّد (له قيمة افتراضية على الخادم).
  const allergens = profile.allergens ?? [];

  const lists = [
    { label: t("medicalHistory"), items: profile.medical_history },
    { label: t("chronic"), items: profile.chronic_diseases },
    { label: t("medications"), items: profile.medications },
  ];

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm" dir="ltr">
          {user.email}
        </p>
      </header>

      <SetupGate profile={profile} />

      <Card>
        <CardHeader
          title={user.full_name}
          action={
            <Link
              href="/onboarding?step=personal"
              className={buttonStyles({ variant: "outline", size: "sm" })}
            >
              {t("edit")}
            </Link>
          }
        />
        <dl className="grid gap-5 sm:grid-cols-3">
          <Row label={t("age")} value={t("ageValue", { years: profile.age_years })} />
          <Row
            label={t("height")}
            value={
              <span className="tabular-nums">
                {formatNumber(locale, profile.height_cm, 1)} {t("cm")}
              </span>
            }
          />
          <Row
            label={t("weight")}
            value={
              <span className="tabular-nums">
                {formatNumber(locale, weight, 1)} {dashboard("kg")}
              </span>
            }
          />
          <Row
            label={t("bmi")}
            value={<span className="tabular-nums">{formatNumber(locale, bmi, 1)}</span>}
          />
          <Row label={t("goal")} value={enums(`goal.${profile.goal}`)} />
          <Row label={t("activity")} value={enums(`activityLevel.${profile.activity_level}`)} />
        </dl>
      </Card>

      <Card>
        <CardHeader title={t("allergens")} />
        <p className="text-sm leading-7">
          {allergens.length === 0
            ? "—"
            : allergens.map((value) => enums(`allergen.${value}`)).join(" · ")}
        </p>
      </Card>

      <Card>
        <CardHeader title={t("medicalHistory")} />
        <dl className="flex flex-col gap-5">
          {lists.map((list) => (
            <Row
              key={list.label}
              label={list.label}
              value={
                list.items.length === 0 ? "—" : list.items.map((item) => String(item)).join(" · ")
              }
            />
          ))}
          {profile.notes !== null && profile.notes !== "" && (
            <Row label={t("notes")} value={profile.notes} />
          )}
        </dl>
      </Card>

      <Card>
        <CardHeader title={consent("title")} />
        {profile.consent_accepted_at === null ? (
          <Alert tone="warning">{consent("required")}</Alert>
        ) : (
          <Alert tone="success">
            {consent("acceptedAt", { date: formatDateTime(locale, profile.consent_accepted_at) })}
          </Alert>
        )}
      </Card>
    </div>
  );
}
