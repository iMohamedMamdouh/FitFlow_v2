import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Alert } from "@/components/ui/alert";
import { Card, CardHeader, Stat } from "@/components/ui/card";
import { getPlatformStats } from "@/lib/api/admin-queries";
import { formatNumber } from "@/lib/format";
import { readLocale } from "@/lib/preferences";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("admin.overview");
  return { title: t("title") };
}

/**
 * نظرة عامة على المنصة.
 *
 * الأرقام مقسومة على أربع كتل بترتيب مقصود: **ما يحتاج تدخّلًا** أولًا
 * لأنه وحده ما قد يستدعي فعلًا اليوم، ثم الحسابات فالخطط فالقاعدة
 * العلمية. لوحة تبدأ بعدد المستخدمين تُقرأ مرة واحدة ثم تُهمَل.
 *
 * استهلاك الذكاء الاصطناعي وتكلفته (10.3) ينتظران المرحلة 6: لا مزوّد
 * بعد، ورقم مختلَق في لوحة إدارة أسوأ من رقم غائب — فالمكان محجوز
 * بجملة صريحة لا ببطاقة أصفار.
 */
export default async function AdminOverviewPage() {
  const t = await getTranslations("admin.overview");
  const roles = await getTranslations("roles");
  const planStatus = await getTranslations("enums.planStatus");
  const locale = await readLocale();

  const stats = await getPlatformStats();
  const number = (value: number) => formatNumber(locale, value, 0);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      <section className="flex flex-col gap-4">
        <h2 className="font-display text-sm font-semibold tracking-tight">
          {t("operationsTitle")}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat
            label={t("awaitingReview")}
            value={number(stats.plans_awaiting_review)}
            tone={stats.plans_awaiting_review > 0 ? "accent" : "default"}
          />
          <Stat
            label={t("unassigned")}
            value={number(stats.patients_without_specialist)}
            tone={stats.patients_without_specialist > 0 ? "accent" : "default"}
          />
          <Stat
            label={t("activeInjuries")}
            value={number(stats.active_injuries)}
            hint={t("acuteInjuries") + ": " + number(stats.acute_injuries)}
          />
          <Stat label={t("logs7")} value={number(stats.logs_last_7_days)} />
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <CardHeader title={t("usersTitle")} />
          <dl className="flex flex-col">
            {stats.users.map((row) => (
              <div
                key={row.role}
                className="border-line flex items-center justify-between gap-4 border-b py-2.5 last:border-b-0"
              >
                <dt className="text-sm">{roles(row.role)}</dt>
                <dd className="text-subtle flex items-center gap-4 text-sm tabular-nums">
                  <span>
                    {t("activeCount")} {number(row.active)}
                  </span>
                  <span className="text-ink font-display font-semibold">{number(row.total)}</span>
                </dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card className="flex flex-col gap-4">
          <CardHeader title={t("plansTitle")} />
          {stats.plans.length === 0 ? (
            <p className="text-subtle text-sm">{t("noPlans")}</p>
          ) : (
            <dl className="flex flex-col">
              {stats.plans.map((row) => (
                <div
                  key={row.status}
                  className="border-line flex items-center justify-between gap-4 border-b py-2.5 last:border-b-0"
                >
                  <dt className="text-sm">{planStatus(row.status)}</dt>
                  <dd className="text-ink font-display text-sm font-semibold tabular-nums">
                    {number(row.total)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </Card>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="font-display text-sm font-semibold tracking-tight">{t("contentTitle")}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label={t("foods")} value={number(stats.catalog_foods)} />
          <Stat label={t("exercises")} value={number(stats.catalog_exercises)} />
          <Stat label={t("injuryTypes")} value={number(stats.catalog_injury_types)} />
          <Stat
            label={t("unreviewed")}
            value={number(stats.catalog_unreviewed)}
            tone={stats.catalog_unreviewed > 0 ? "accent" : "default"}
          />
        </div>
        {stats.catalog_unreviewed > 0 && <Alert tone="warning">{t("unreviewedHint")}</Alert>}
      </section>

      <Alert tone="info">{t("aiPending")}</Alert>
    </div>
  );
}
