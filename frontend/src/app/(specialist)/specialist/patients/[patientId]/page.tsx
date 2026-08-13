import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { TrendChart, type TrendPoint } from "@/components/charts/trend-chart";
import { PatientFlagBadge } from "@/components/specialist/patient-flag";
import { Alert, Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader, Stat } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import {
  getPatientAudit,
  getPatientInjuries,
  getPatientLogs,
  getPatientNotes,
  getPatientPlans,
  getPatientProfile,
  getPatientReadings,
  getPatientSummary,
  getInjuryTypes,
} from "@/lib/api/specialist-queries";
import {
  bodyMassIndex,
  formatDate,
  formatDateTime,
  formatDelta,
  formatNumber,
  toNumber,
} from "@/lib/format";
import { isAuditActionKey } from "@/i18n/messages";
import { readLocale } from "@/lib/preferences";
import type { DailyLogRead, ReadingRead } from "@/lib/api/schema";
import { NoteForm } from "./note-form";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ patientId: string }>;
}): Promise<Metadata> {
  const { patientId } = await params;
  const summary = await getPatientSummary(patientId);
  return { title: summary?.full_name ?? "—" };
}

function weightSeries(readings: readonly ReadingRead[]): TrendPoint[] {
  return readings
    .filter((reading) => reading.weight_kg !== null)
    .map((reading) => ({ date: reading.reading_date, value: Number(reading.weight_kg) }))
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

export default async function PatientRecordPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  const t = await getTranslations("specialist.patient");
  const notesText = await getTranslations("specialist.notes");
  const auditText = await getTranslations("specialist.audit");
  const auditActions = await getTranslations("auditActions");
  const profileText = await getTranslations("profile");
  const dashboard = await getTranslations("dashboard");
  const enums = await getTranslations("enums");
  const common = await getTranslations("common");
  const locale = await readLocale();

  const summary = await getPatientSummary(patientId);
  // غياب المريض من قائمة الأخصائي = ليس مسنَدًا له. نفس رد الخادم: 404
  // لا 403، فلا يصبح الرابط أداة لمعرفة أي المعرّفات موجود.
  if (summary === null) notFound();

  const [profile, injuries, injuryTypes, readings, logs, plans, notes, audit] = await Promise.all([
    getPatientProfile(patientId),
    getPatientInjuries(patientId),
    getInjuryTypes(),
    getPatientReadings(patientId),
    getPatientLogs(patientId),
    getPatientPlans(patientId),
    getPatientNotes(patientId),
    getPatientAudit(patientId),
  ]);

  const injuryName = new Map(injuryTypes.map((type) => [type.id, type.name_ar]));
  const latestWeight = readings.find((reading) => reading.weight_kg !== null)?.weight_kg ?? null;
  const bmi = profile === null ? null : bodyMassIndex(latestWeight, profile.height_cm);
  const change = toNumber(summary.weight_change_kg);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Link href="/specialist" className="text-subtle hover:text-ink text-sm transition-colors">
          ← {t("back")}
        </Link>
      </div>

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
            {summary.full_name}
          </h1>
          <p className="text-subtle mt-1.5 text-sm" dir="ltr">
            {summary.email}
          </p>
        </div>
        <PatientFlagBadge flag={summary.flag} />
      </header>

      {/* المساءلة تُقال للأخصائي لا تُخفى عنه: من يعرف أن اطّلاعه مسجَّل
          يفتح ما يحتاجه فقط. */}
      <Alert tone="info">{t("viewedNotice")}</Alert>

      <section className="grid gap-4 sm:grid-cols-4">
        <Stat
          label={dashboard("currentWeight")}
          value={`${formatNumber(locale, latestWeight, 1)} ${dashboard("kg")}`}
        />
        <Stat
          label={dashboard("change")}
          value={`${formatDelta(locale, change)} ${dashboard("kg")}`}
        />
        <Stat label={profileText("bmi")} value={formatNumber(locale, bmi, 1)} />
        <Stat
          label={notesText("title")}
          value={formatNumber(locale, notes.length)}
          hint={summary.plans_awaiting_review > 0 ? enums("planStatus.pending_review") : undefined}
        />
      </section>

      {/* ------------------------------------------------ الملف الشخصي */}
      <Card>
        <CardHeader title={t("profile")} />
        {profile === null ? (
          <Alert tone="warning">{t("noProfile")}</Alert>
        ) : (
          <dl className="grid gap-5 sm:grid-cols-3">
            {[
              {
                label: profileText("age"),
                value: profileText("ageValue", { years: profile.age_years }),
              },
              {
                label: profileText("height"),
                value: `${formatNumber(locale, profile.height_cm, 1)} ${profileText("cm")}`,
              },
              { label: profileText("goal"), value: enums(`goal.${profile.goal}`) },
              {
                label: profileText("activity"),
                value: enums(`activityLevel.${profile.activity_level}`),
              },
              {
                label: profileText("allergens"),
                value:
                  (profile.allergens ?? []).length === 0
                    ? "—"
                    : (profile.allergens ?? [])
                        .map((value) => enums(`allergen.${value}`))
                        .join(" · "),
              },
              {
                label: profileText("chronic"),
                value:
                  profile.chronic_diseases.length === 0
                    ? "—"
                    : profile.chronic_diseases.map((item) => String(item)).join(" · "),
              },
              {
                label: profileText("medications"),
                value:
                  profile.medications.length === 0
                    ? "—"
                    : profile.medications.map((item) => String(item)).join(" · "),
              },
              {
                label: profileText("medicalHistory"),
                value:
                  profile.medical_history.length === 0
                    ? "—"
                    : profile.medical_history.map((item) => String(item)).join(" · "),
              },
            ].map((row) => (
              <div key={row.label}>
                <dt className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
                  {row.label}
                </dt>
                <dd className="mt-1.5 text-sm leading-7">{row.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </Card>

      {/* ------------------------------------------------------ الرسوم */}
      <section className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title={t("weightChart")} />
          <TrendChart points={weightSeries(readings)} unit={dashboard("kg")} />
        </Card>
        <Card>
          <CardHeader title={t("painChart")} />
          <TrendChart
            points={logSeries(logs, "pain_level")}
            color="var(--color-critical)"
            fractionDigits={0}
            domain={[0, 10]}
          />
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title={t("adherenceChart")} />
          <TrendChart
            points={logSeries(logs, "diet_adherence_pct")}
            color="var(--color-caution)"
            fractionDigits={0}
            domain={[0, 100]}
            unit="%"
          />
        </Card>
      </section>

      {/* --------------------------------------------------- الإصابات */}
      <Card>
        <CardHeader title={t("injuries")} />
        {injuries.length === 0 ? (
          <p className="text-subtle text-sm">{t("noInjuries")}</p>
        ) : (
          <ul className="divide-line flex flex-col divide-y text-sm">
            {injuries.map((injury) => (
              <li key={injury.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
                <span className="font-medium">
                  {injuryName.get(injury.injury_type_id) ?? common("unknown")}
                </span>
                <Badge tone={injury.status === "acute" ? "danger" : "neutral"}>
                  {enums(`injuryStatus.${injury.status}`)}
                </Badge>
                <span className="text-subtle tabular-nums">
                  {formatDate(locale, injury.injury_date)} · {injury.pain_level}/10
                </span>
                <span className="text-faint">{enums(`bodySide.${injury.side}`)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* ------------------------------------------------------ الخطط */}
      <Card>
        <CardHeader title={t("plans")} />
        {plans.length === 0 ? (
          <p className="text-subtle text-sm">{t("noPlans")}</p>
        ) : (
          <ul className="divide-line flex flex-col divide-y text-sm">
            {plans.map((plan) => (
              <li key={plan.id} className="flex flex-wrap items-center gap-3 py-2.5">
                <span className="tabular-nums">{formatDate(locale, plan.created_at)}</span>
                <Badge tone={plan.status === "active" ? "success" : "neutral"}>
                  {enums(`planStatus.${plan.status}`)}
                </Badge>
                <span className="text-faint">{enums(`planType.${plan.plan_type}`)}</span>
                <Link
                  href={`/specialist/plans/${plan.id}`}
                  className={buttonStyles({ variant: "quiet", size: "sm", className: "ms-auto" })}
                >
                  {t("openPlan")}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* --------------------------------------------------- التسجيل */}
      <Card>
        <CardHeader title={t("logs")} />
        {logs.length === 0 ? (
          <p className="text-subtle text-sm">{t("noLogs")}</p>
        ) : (
          <ul className="divide-line flex flex-col divide-y text-sm">
            {logs.slice(0, 14).map((log) => (
              <li key={log.id} className="flex flex-wrap items-center gap-x-5 gap-y-1 py-2.5">
                <span className="font-medium tabular-nums">{formatDate(locale, log.log_date)}</span>
                {log.weight_kg !== null && (
                  <span className="text-subtle tabular-nums">
                    {formatNumber(locale, log.weight_kg, 1)} {dashboard("kg")}
                  </span>
                )}
                {log.pain_level !== null && (
                  <span className="text-subtle tabular-nums">{log.pain_level}/10</span>
                )}
                {log.diet_adherence_pct !== null && (
                  <span className="text-subtle tabular-nums">{log.diet_adherence_pct}%</span>
                )}
                {log.notes !== null && log.notes !== "" && (
                  <span className="text-faint">{log.notes}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* ------------------------------------------------- الملاحظات */}
      <Card>
        <CardHeader title={notesText("title")} />
        <NoteForm patientId={patientId} />
        {notes.length === 0 ? (
          <p className="text-subtle mt-5 text-sm">{t("noNotes")}</p>
        ) : (
          <ul className="divide-line mt-5 flex flex-col divide-y text-sm">
            {notes.map((note) => (
              <li key={note.id} className="flex flex-col gap-1.5 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-faint text-xs tabular-nums">
                    {formatDateTime(locale, note.created_at)}
                  </span>
                  {note.is_internal && <Badge tone="warning">{notesText("internalBadge")}</Badge>}
                </div>
                <p className="leading-7">{note.note}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* --------------------------------------------- سجل التدقيق */}
      <Card>
        <CardHeader title={t("audit")} description={auditText("subtitle")} />
        {audit.length === 0 ? (
          <p className="text-subtle text-sm">{t("noAudit")}</p>
        ) : (
          <ul className="divide-line flex flex-col divide-y text-sm">
            {audit.map((entry) => (
              <li key={entry.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-2.5">
                <span className="text-faint w-40 shrink-0 text-xs tabular-nums">
                  {formatDateTime(locale, entry.created_at)}
                </span>
                <span className="font-medium">
                  {isAuditActionKey(entry.action) ? auditActions(entry.action) : entry.action}
                </span>
                <span className="text-subtle ms-auto text-xs">
                  {entry.actor_name ?? auditText("system")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
