import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { TrendChart, type TrendPoint } from "@/components/charts/trend-chart";
import { GeneratePlanForm } from "@/components/generate-plan-form";
import { MedicalDisclaimer } from "@/components/medical-disclaimer";
import { SetupGate, isReadyForPlan } from "@/components/setup-gate";
import { Link } from "@/components/ui/nav-link";
import { Alert, Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader, Stat } from "@/components/ui/card";
import {
  firstWeight,
  getActivePlan,
  getCurrentUser,
  getDailyLogs,
  getProfile,
  getReadings,
  latestWeight,
} from "@/lib/api/queries";
import { formatDelta, formatNumber, toNumber } from "@/lib/format";
import type { DailyLogRead, ReadingRead } from "@/lib/api/schema";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("dashboard");
  return { title: t("title") };
}

/** الرسوم تُقرأ من الأقدم للأحدث، والـ API يرجّع الأحدث أولًا. */
function weightSeries(readings: readonly ReadingRead[]): TrendPoint[] {
  return readings
    .filter((reading) => reading.weight_kg !== null)
    .map((reading) => ({
      date: reading.reading_date,
      value: Number(reading.weight_kg),
    }))
    .filter((point) => Number.isFinite(point.value))
    .reverse();
}

function logSeries(
  logs: readonly DailyLogRead[],
  field: "pain_level" | "diet_adherence_pct",
): TrendPoint[] {
  return logs
    .filter((log) => log[field] !== null)
    .map((log) => ({ date: log.log_date, value: Number(log[field]) }))
    .reverse();
}

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");
  const planText = await getTranslations("plan");
  const enums = await getTranslations("enums");

  const [user, profile, readings, logs, plan] = await Promise.all([
    getCurrentUser(),
    getProfile(),
    getReadings(),
    getDailyLogs(),
    getActivePlan(),
  ]);

  const current = toNumber(latestWeight(readings));
  const start = toNumber(firstWeight(readings));
  const change = current !== null && start !== null ? current - start : null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-bold">{t("greeting", { name: user.full_name })}</h1>
        <p className="text-muted text-sm">{t("title")}</p>
      </header>

      <SetupGate profile={profile} />
      <MedicalDisclaimer />

      <section className="grid gap-4 sm:grid-cols-3">
        <Stat
          label={t("currentWeight")}
          value={`${formatNumber(current, 1)} ${t("kg")}`}
          hint={start !== null ? `${t("startWeight")}: ${formatNumber(start, 1)}` : undefined}
        />
        <Stat label={t("change")} value={`${formatDelta(change)} ${t("kg")}`} />
        <Stat
          label={t("dailyCalories")}
          value={
            plan?.nutrition != null
              ? `${formatNumber(plan.nutrition.daily_calories)} ${t("kcal")}`
              : "—"
          }
          hint={plan !== null ? enums(`planStatus.${plan.status}`) : t("noActivePlan")}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title={t("weightChart")} />
          <TrendChart points={weightSeries(readings)} unit={t("kg")} />
        </Card>
        <Card>
          <CardHeader title={t("painChart")} />
          <TrendChart
            points={logSeries(logs, "pain_level")}
            color="var(--color-danger)"
            fractionDigits={0}
            domain={[0, 10]}
          />
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title={t("adherenceChart")} />
          <TrendChart
            points={logSeries(logs, "diet_adherence_pct")}
            color="var(--color-info)"
            fractionDigits={0}
            domain={[0, 100]}
            unit="%"
          />
        </Card>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader title={t("activePlan")} />
          {plan === null ? (
            <Alert tone="info">{planText("emptyHint")}</Alert>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={plan.status === "active" ? "success" : "primary"}>
                  {enums(`planStatus.${plan.status}`)}
                </Badge>
                <Badge>{enums(`planType.${plan.plan_type}`)}</Badge>
              </div>
              <Link href="/plan" className={buttonStyles({ variant: "outline", size: "sm" })}>
                {planText("title")}
              </Link>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title={t("quickActions")} />
          <div className="flex flex-col gap-3">
            <Link href="/log" className={buttonStyles({ variant: "outline" })}>
              {t("logToday")}
            </Link>
            <GeneratePlanForm disabled={!isReadyForPlan(profile)} />
          </div>
        </Card>
      </section>
    </div>
  );
}
