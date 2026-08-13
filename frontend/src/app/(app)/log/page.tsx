import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { SetupGate } from "@/components/setup-gate";
import { Card, CardHeader } from "@/components/ui/card";
import { getDailyLogs, getProfile, getReadings, latestWeight } from "@/lib/api/queries";
import { formatDate, formatNumber, todayIso } from "@/lib/format";
import { LogForm } from "./log-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("log");
  return { title: t("title") };
}

export default async function LogPage() {
  const t = await getTranslations("log");
  const [profile, readings, logs] = await Promise.all([
    getProfile(),
    getReadings(1),
    getDailyLogs(14),
  ]);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-bold">{t("title")}</h1>
        <p className="text-muted text-sm leading-7">{t("subtitle")}</p>
      </header>

      <SetupGate profile={profile} />

      <Card>
        <LogForm today={todayIso()} currentWeight={latestWeight(readings)} />
      </Card>

      <Card>
        <CardHeader title={t("recent")} />
        {logs.length === 0 ? (
          <p className="text-muted text-sm">{t("noEntries")}</p>
        ) : (
          <ul className="flex flex-col divide-y divide-[var(--color-border)] text-sm">
            {logs.map((log) => (
              <li key={log.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-2">
                <span className="font-medium">{formatDate(log.log_date)}</span>
                <span className="text-muted tabular-nums">
                  {log.weight_kg !== null && `${formatNumber(log.weight_kg, 1)} كجم`}
                </span>
                <span className="text-muted tabular-nums">
                  {log.pain_level !== null && `${t("pain")}: ${log.pain_level}/10`}
                </span>
                <span className="text-muted tabular-nums">
                  {log.diet_adherence_pct !== null && `${log.diet_adherence_pct}%`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
