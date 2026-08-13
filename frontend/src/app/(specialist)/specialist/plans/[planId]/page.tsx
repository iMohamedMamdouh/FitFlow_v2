import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Alert, Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader, Stat } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { MEAL_ORDER, type MealRead } from "@/lib/api/schema";
import { getMyPatients, getPlanForReview, getPlanHistory } from "@/lib/api/specialist-queries";
import { formatDateTime, formatNumber } from "@/lib/format";
import { readLocale } from "@/lib/preferences";
import { ReviewForm } from "./review-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("specialist.plan");
  return { title: t("title") };
}

function orderMeals(meals: readonly MealRead[]): MealRead[] {
  return [...meals].sort(
    (left, right) => MEAL_ORDER.indexOf(left.slot) - MEAL_ORDER.indexOf(right.slot),
  );
}

export default async function PlanReviewPage({ params }: { params: Promise<{ planId: string }> }) {
  const { planId } = await params;
  const t = await getTranslations("specialist.plan");
  const planText = await getTranslations("plan");
  const enums = await getTranslations("enums");
  const common = await getTranslations("common");
  const locale = await readLocale();

  const plan = await getPlanForReview(planId);
  if (plan === null) notFound();

  const [history, patients] = await Promise.all([getPlanHistory(planId), getMyPatients()]);
  const patient = patients.find((entry) => entry.id === plan.user_id);
  const nutrition = plan.nutrition ?? null;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-7">
      <div>
        <Link
          href="/specialist/review"
          className="text-subtle hover:text-ink text-sm transition-colors"
        >
          ← {t("title")}
        </Link>
      </div>

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
            {t("title")}
          </h1>
          <p className="text-subtle mt-1.5 text-sm">
            {patient === undefined ? (
              common("unknown")
            ) : (
              <Link
                href={`/specialist/patients/${patient.id}`}
                className="text-accent hover:underline"
              >
                {t("forPatient", { name: patient.full_name })}
              </Link>
            )}
          </p>
        </div>
        <Badge tone={plan.status === "active" ? "success" : "clay"}>
          {enums(`planStatus.${plan.status}`)}
        </Badge>
      </header>

      {/* الحالة تُقال صراحةً: الفرق بين "معتمدة" و"مفعّلة" هو الفرق بين
          قرار اتُّخذ وقرار وصل المريض، وخلطهما يعني خطة يظنّها الأخصائي
          مسلَّمة وهي ليست كذلك. */}
      <Alert tone={plan.status === "active" ? "success" : "info"}>
        {plan.status === "active" ? t("visibleNow") : t("notVisibleYet")}
      </Alert>

      <Card>
        <CardHeader
          title={t("decision")}
          description={`${planText("createdAt")}: ${formatDateTime(locale, plan.created_at)} · ${planText("engineVersion")} ${plan.rule_engine_version}`}
        />
        <ReviewForm planId={plan.id} status={plan.status} />
      </Card>

      <Card>
        <CardHeader title={planText("targets")} />
        {nutrition === null ? (
          <Alert tone="info">{planText("emptyHint")}</Alert>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-4">
              <Stat
                tone="accent"
                label={planText("calories")}
                value={formatNumber(locale, nutrition.daily_calories)}
              />
              <Stat
                label={planText("protein")}
                value={`${formatNumber(locale, nutrition.protein_g, 1)} ${planText("grams")}`}
              />
              <Stat
                label={planText("carbs")}
                value={`${formatNumber(locale, nutrition.carbs_g, 1)} ${planText("grams")}`}
              />
              <Stat
                label={planText("fat")}
                value={`${formatNumber(locale, nutrition.fat_g, 1)} ${planText("grams")}`}
              />
            </div>
            {nutrition.notes_ar !== null && nutrition.notes_ar !== "" && (
              <p className="text-subtle mt-5 text-sm leading-7">{nutrition.notes_ar}</p>
            )}
          </>
        )}
      </Card>

      <section className="grid gap-4 sm:grid-cols-2">
        {orderMeals(plan.meals ?? []).map((meal) => (
          <Card key={meal.slot}>
            <CardHeader
              title={enums(`mealSlot.${meal.slot}`)}
              description={planText("mealCalories", {
                calories: formatNumber(locale, meal.calories),
              })}
            />
            <ul className="divide-line flex flex-col divide-y text-sm">
              {meal.items.map((item) => (
                <li key={item.food_id} className="flex items-center justify-between gap-3 py-2.5">
                  <span>{item.name_ar}</span>
                  <span className="text-subtle whitespace-nowrap tabular-nums">
                    {formatNumber(locale, item.grams, 0)} {planText("grams")} ·{" "}
                    {formatNumber(locale, item.calories, 0)}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </section>

      <Card>
        <CardHeader title={t("transitions")} />
        <ol className="divide-line flex flex-col divide-y text-sm">
          {history.map((entry) => (
            <li key={`${entry.created_at}-${entry.to_status}`} className="flex flex-col gap-1 py-3">
              <div className="flex flex-wrap items-center gap-2">
                {entry.from_status !== null && (
                  <span className="text-faint">{enums(`planStatus.${entry.from_status}`)} →</span>
                )}
                <Badge tone={entry.to_status === "active" ? "success" : "neutral"}>
                  {enums(`planStatus.${entry.to_status}`)}
                </Badge>
                <span className="text-faint text-xs tabular-nums">
                  {formatDateTime(locale, entry.created_at)}
                </span>
              </div>
              {entry.reason !== null && entry.reason !== "" && (
                <p className="text-subtle leading-6">{entry.reason}</p>
              )}
            </li>
          ))}
        </ol>
      </Card>

      {patient !== undefined && (
        <Link
          href={`/specialist/patients/${patient.id}`}
          className={buttonStyles({ variant: "outline" })}
        >
          {t("forPatient", { name: patient.full_name })}
        </Link>
      )}
    </div>
  );
}
