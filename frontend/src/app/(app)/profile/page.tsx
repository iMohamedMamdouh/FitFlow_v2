import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { SetupGate } from "@/components/setup-gate";
import { Link } from "@/components/ui/nav-link";
import { Alert } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { getCurrentUser, getProfile, getReadings, latestWeight } from "@/lib/api/queries";
import { bodyMassIndex, formatDateTime, formatNumber } from "@/lib/format";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("profile");
  return { title: t("title") };
}

function List({ label, items }: { label: string; items: readonly unknown[] }) {
  return (
    <div>
      <dt className="text-muted text-sm">{label}</dt>
      <dd className="text-sm leading-7">
        {items.length === 0 ? "—" : items.map((item) => String(item)).join(" • ")}
      </dd>
    </div>
  );
}

export default async function ProfilePage() {
  const t = await getTranslations("profile");
  const enums = await getTranslations("enums");
  const consent = await getTranslations("consent");

  const [user, profile, readings] = await Promise.all([
    getCurrentUser(),
    getProfile(),
    getReadings(1),
  ]);

  if (profile === null) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-5">
        <h1 className="text-xl font-bold">{t("title")}</h1>
        <SetupGate profile={null} />
      </div>
    );
  }

  const weight = latestWeight(readings);
  const bmi = bodyMassIndex(weight, profile.height_cm);
  // `allergens` اختياري في المخطط المولَّد (له قيمة افتراضية على الخادم).
  const allergens = profile.allergens ?? [];

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-5">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-bold">{t("title")}</h1>
        <p className="text-muted text-sm" dir="ltr">
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
        <dl className="grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-muted text-sm">{t("age")}</dt>
            <dd className="text-sm">{t("ageValue", { years: profile.age_years })}</dd>
          </div>
          <div>
            <dt className="text-muted text-sm">{t("height")}</dt>
            <dd className="text-sm tabular-nums">{formatNumber(profile.height_cm, 1)} سم</dd>
          </div>
          <div>
            <dt className="text-muted text-sm">{t("weight")}</dt>
            <dd className="text-sm tabular-nums">{formatNumber(weight, 1)} كجم</dd>
          </div>
          <div>
            <dt className="text-muted text-sm">{t("bmi")}</dt>
            <dd className="text-sm tabular-nums">{formatNumber(bmi, 1)}</dd>
          </div>
          <div>
            <dt className="text-muted text-sm">{t("goal")}</dt>
            <dd className="text-sm">{enums(`goal.${profile.goal}`)}</dd>
          </div>
          <div>
            <dt className="text-muted text-sm">{t("activity")}</dt>
            <dd className="text-sm">{enums(`activityLevel.${profile.activity_level}`)}</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <CardHeader title={t("allergens")} />
        <p className="text-sm leading-7">
          {allergens.length === 0
            ? "—"
            : allergens.map((value) => enums(`allergen.${value}`)).join(" • ")}
        </p>
      </Card>

      <Card>
        <CardHeader title={t("medicalHistory")} />
        <dl className="flex flex-col gap-3">
          <List label={t("medicalHistory")} items={profile.medical_history} />
          <List label={t("chronic")} items={profile.chronic_diseases} />
          <List label={t("medications")} items={profile.medications} />
          {profile.notes !== null && profile.notes !== "" && (
            <div>
              <dt className="text-muted text-sm">{t("notes")}</dt>
              <dd className="text-sm leading-7">{profile.notes}</dd>
            </div>
          )}
        </dl>
      </Card>

      <Card>
        <CardHeader title={consent("title")} />
        {profile.consent_accepted_at === null ? (
          <Alert tone="warning">{consent("required")}</Alert>
        ) : (
          <Alert tone="success">
            {consent("acceptedAt", { date: formatDateTime(profile.consent_accepted_at) })}
          </Alert>
        )}
      </Card>
    </div>
  );
}
