import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { SetupGate } from "@/components/setup-gate";
import { Card, CardHeader } from "@/components/ui/card";
import { getDailyLogs, getProfile, getReadings, latestWeight } from "@/lib/api/queries";
import { formatDate, formatNumber, todayIso } from "@/lib/format";
import { readLocale } from "@/lib/preferences";
import { LogForm } from "./log-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("log");
  return { title: t("title") };
}

export default async function LogPage() {
  const t = await getTranslations("log");
  const dashboard = await getTranslations("dashboard");
  const locale = await readLocale();

  const [profile, readings, logs] = await Promise.all([
    getProfile(),
    getReadings(1),
    getDailyLogs(14),
  ]);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      <SetupGate profile={profile} />

      <Card>
        <LogForm today={todayIso()} currentWeight={latestWeight(readings)} />
      </Card>

      <Card>
        <CardHeader title={t("recent")} />
        {logs.length === 0 ? (
          <p className="text-subtle text-sm">{t("noEntries")}</p>
        ) : (
          <ul className="divide-line flex flex-col divide-y text-sm">
            {logs.map((log) => (
              <li key={log.id} className="flex flex-wrap items-center gap-x-5 gap-y-1 py-2.5">
                <span className="font-medium tabular-nums">{formatDate(locale, log.log_date)}</span>
                {log.weight_kg !== null && (
                  <span className="text-subtle tabular-nums">
                    {formatNumber(locale, log.weight_kg, 1)} {dashboard("kg")}
                  </span>
                )}
                {log.pain_level !== null && (
                  <span className="text-subtle tabular-nums">
                    {t("pain")}: {log.pain_level}/10
                  </span>
                )}
                {log.diet_adherence_pct !== null && (
                  <span className="text-subtle tabular-nums">{log.diet_adherence_pct}%</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
