import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { GeneratePlanForm } from "@/components/generate-plan-form";
import { MedicalDisclaimer } from "@/components/medical-disclaimer";
import { SetupGate, isReadyForPlan } from "@/components/setup-gate";
import { Alert, Badge } from "@/components/ui/alert";
import { Card, CardHeader, Stat } from "@/components/ui/card";
import { getActivePlan, getMyPlans, getProfile } from "@/lib/api/queries";
import { formatDate, formatNumber } from "@/lib/format";
import { readLocale } from "@/lib/preferences";
import { MEAL_ORDER, type MealRead } from "@/lib/api/schema";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("plan");
  return { title: t("title") };
}

/** ترتيب الوجبات بترتيب اليوم لا بترتيب وصولها من الـ API. */
function orderMeals(meals: readonly MealRead[]): MealRead[] {
  return [...meals].sort(
    (left, right) => MEAL_ORDER.indexOf(left.slot) - MEAL_ORDER.indexOf(right.slot),
  );
}

export default async function PlanPage() {
  const t = await getTranslations("plan");
  const enums = await getTranslations("enums");
  const locale = await readLocale();

  const [profile, plan, plans] = await Promise.all([getProfile(), getActivePlan(), getMyPlans()]);
  const nutrition = plan?.nutrition ?? null;

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
      </header>

      <SetupGate profile={profile} />
      <MedicalDisclaimer />

      {plan === null ? (
        <Card>
          <CardHeader title={t("empty")} description={t("emptyHint")} />
          <GeneratePlanForm disabled={!isReadyForPlan(profile)} />
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader
              title={t("targets")}
              description={`${t("createdAt")}: ${formatDate(locale, plan.created_at)} · ${t("engineVersion")} ${plan.rule_engine_version}`}
              action={
                <Badge tone={plan.status === "active" ? "success" : "accent"}>
                  {enums(`planStatus.${plan.status}`)}
                </Badge>
              }
            />
            {nutrition === null ? (
              <Alert tone="info">{t("emptyHint")}</Alert>
            ) : (
              <>
                <div className="grid gap-4 sm:grid-cols-4">
                  <Stat
                    tone="accent"
                    label={t("calories")}
                    value={formatNumber(locale, nutrition.daily_calories)}
                  />
                  <Stat
                    label={t("protein")}
                    value={`${formatNumber(locale, nutrition.protein_g, 1)} ${t("grams")}`}
                  />
                  <Stat
                    label={t("carbs")}
                    value={`${formatNumber(locale, nutrition.carbs_g, 1)} ${t("grams")}`}
                  />
                  <Stat
                    label={t("fat")}
                    value={`${formatNumber(locale, nutrition.fat_g, 1)} ${t("grams")}`}
                  />
                </div>
                {nutrition.notes_ar !== null && nutrition.notes_ar !== "" && (
                  <p className="text-subtle mt-5 text-sm leading-7">{nutrition.notes_ar}</p>
                )}
              </>
            )}
            {plan.review_notes != null && plan.review_notes !== "" && (
              <Alert tone="info" className="mt-5" title={t("reviewNotes")}>
                {plan.review_notes}
              </Alert>
            )}
          </Card>

          <section className="grid gap-5 sm:grid-cols-2">
            {orderMeals(plan.meals ?? []).map((meal) => (
              <Card key={meal.slot}>
                <CardHeader
                  title={enums(`mealSlot.${meal.slot}`)}
                  description={t("mealCalories", {
                    calories: formatNumber(locale, meal.calories),
                  })}
                />
                <ul className="divide-line flex flex-col divide-y text-sm">
                  {meal.items.map((item) => (
                    <li
                      key={item.food_id}
                      className="flex items-center justify-between gap-3 py-2.5"
                    >
                      <span>{item.name_ar}</span>
                      <span className="text-subtle whitespace-nowrap tabular-nums">
                        {formatNumber(locale, item.grams, 0)} {t("grams")} ·{" "}
                        {formatNumber(locale, item.calories, 0)}
                      </span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </section>

          <Card>
            <CardHeader title={t("history")} />
            <ul className="divide-line flex flex-col divide-y text-sm">
              {plans.map((entry) => (
                <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5">
                  <span className="tabular-nums">{formatDate(locale, entry.created_at)}</span>
                  <Badge tone={entry.status === "active" ? "success" : "neutral"}>
                    {enums(`planStatus.${entry.status}`)}
                  </Badge>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <CardHeader title={t("generate")} />
            <GeneratePlanForm disabled={!isReadyForPlan(profile)} />
          </Card>
        </>
      )}
    </div>
  );
}
