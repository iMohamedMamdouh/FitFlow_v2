import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { PatientFlagBadge } from "@/components/specialist/patient-flag";
import { Alert, Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { getMyPatients, getReviewQueue } from "@/lib/api/specialist-queries";
import { formatDelta, formatNumber, toNumber } from "@/lib/format";
import { readLocale } from "@/lib/preferences";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("specialist.patients");
  return { title: t("title") };
}

export default async function PatientsPage() {
  const t = await getTranslations("specialist.patients");
  const review = await getTranslations("specialist.review");
  const dashboard = await getTranslations("dashboard");
  const locale = await readLocale();

  const [patients, queue] = await Promise.all([getMyPatients(), getReviewQueue()]);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1.5">
        <span className="text-faint text-[0.7rem] font-semibold tracking-[0.14em] uppercase">
          {t("count", { count: patients.length })}
        </span>
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      {queue.length > 0 && (
        <Alert tone="warning">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span>{t("awaiting", { count: queue.length })}</span>
            <Link href="/specialist/review" className={buttonStyles({ size: "sm" })}>
              {review("title")}
            </Link>
          </div>
        </Alert>
      )}

      {patients.length === 0 ? (
        <Card>
          <CardHeader title={t("empty")} description={t("emptyHint")} />
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {patients.map((patient) => {
            const change = toNumber(patient.weight_change_kg);
            return (
              <Card key={patient.id} className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="font-display truncate font-semibold tracking-tight">
                      {patient.full_name}
                    </h2>
                    <p className="text-faint truncate text-xs" dir="ltr">
                      {patient.email}
                    </p>
                  </div>
                  <PatientFlagBadge flag={patient.flag} />
                </div>

                <dl className="grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <dt className="text-faint text-[0.65rem] font-semibold tracking-[0.1em] uppercase">
                      {dashboard("currentWeight")}
                    </dt>
                    <dd className="mt-1 tabular-nums">
                      {patient.latest_weight_kg === null
                        ? t("noWeight")
                        : `${formatNumber(locale, patient.latest_weight_kg, 1)} ${dashboard("kg")}`}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faint text-[0.65rem] font-semibold tracking-[0.1em] uppercase">
                      {dashboard("change")}
                    </dt>
                    <dd className="mt-1 tabular-nums">
                      {change === null ? "—" : `${formatDelta(locale, change)} ${dashboard("kg")}`}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faint text-[0.65rem] font-semibold tracking-[0.1em] uppercase">
                      {t("lastLog")}
                    </dt>
                    <dd className="mt-1 tabular-nums">
                      {patient.days_since_last_log === null
                        ? t("noLog")
                        : patient.days_since_last_log === 0
                          ? t("today")
                          : t("daysAgo", { days: patient.days_since_last_log })}
                    </dd>
                  </div>
                </dl>

                <div className="flex flex-wrap items-center gap-2">
                  {patient.diet_adherence_avg !== null && (
                    <Badge tone={patient.diet_adherence_avg >= 70 ? "success" : "warning"}>
                      {t("adherence")} {patient.diet_adherence_avg}%
                    </Badge>
                  )}
                  {patient.active_injuries > 0 && (
                    <Badge tone={patient.has_acute_injury ? "danger" : "neutral"}>
                      {patient.active_injuries}
                    </Badge>
                  )}
                  <Link
                    href={`/specialist/patients/${patient.id}`}
                    className={buttonStyles({
                      variant: "outline",
                      size: "sm",
                      className: "ms-auto",
                    })}
                  >
                    {t("open")}
                  </Link>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
