import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { SetupGate } from "@/components/setup-gate";
import { Alert, Badge } from "@/components/ui/alert";
import { Card, CardHeader } from "@/components/ui/card";
import { apiFetch } from "@/lib/api/server";
import { getInjuries, getInjuryTypes, getProfile } from "@/lib/api/queries";
import { formatDate, formatNumber, todayIso } from "@/lib/format";
import { readLocale } from "@/lib/preferences";
import type { AttachmentRead, InjuryRead, InjuryTypeRead } from "@/lib/api/schema";
import { AttachmentUpload } from "./attachment-upload";
import { InjuryForm } from "./injury-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("injuries");
  return { title: t("title") };
}

function typeOf(injury: InjuryRead, types: readonly InjuryTypeRead[]): InjuryTypeRead | undefined {
  return types.find((type) => type.id === injury.injury_type_id);
}

async function InjuryCard({
  injury,
  injuryTypes,
}: {
  injury: InjuryRead;
  injuryTypes: readonly InjuryTypeRead[];
}) {
  const t = await getTranslations("injuries");
  const enums = await getTranslations("enums");
  const common = await getTranslations("common");
  const locale = await readLocale();

  const injuryType = typeOf(injury, injuryTypes);
  const attachments = await apiFetch<AttachmentRead[]>(`/me/injuries/${injury.id}/attachments`);

  return (
    <Card>
      <CardHeader
        title={injuryType?.name_ar ?? common("unknown")}
        description={`${formatDate(locale, injury.injury_date)} · ${t("phase", { phase: injury.current_phase })}`}
        action={
          <Badge tone={injury.status === "acute" ? "danger" : "neutral"}>
            {enums(`injuryStatus.${injury.status}`)}
          </Badge>
        }
      />

      <dl className="grid gap-4 text-sm sm:grid-cols-3">
        {[
          { label: t("pain"), value: `${injury.pain_level}/10` },
          { label: t("side"), value: enums(`bodySide.${injury.side}`) },
          {
            label: t("hadSurgery"),
            value: injury.had_surgery ? formatDate(locale, injury.surgery_date) : common("no"),
          },
        ].map((row) => (
          <div key={row.label}>
            <dt className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
              {row.label}
            </dt>
            <dd className="mt-1 tabular-nums">{row.value}</dd>
          </div>
        ))}
      </dl>

      {injury.notes !== null && injury.notes !== "" && (
        <p className="text-subtle mt-4 text-sm leading-7">{injury.notes}</p>
      )}

      {injury.status === "acute" && (
        <Alert tone="warning" className="mt-4">
          {t("acuteWarning")}
        </Alert>
      )}

      <section className="border-line mt-6 border-t pt-5">
        <h3 className="font-display text-sm font-semibold tracking-tight">
          {t("attachments.title")}
        </h3>
        {attachments.length === 0 ? (
          <p className="text-subtle mt-2 text-sm">{t("attachments.empty")}</p>
        ) : (
          <ul className="divide-line mt-2 flex flex-col divide-y text-sm">
            {attachments.map((attachment) => (
              <li key={attachment.id} className="flex items-center justify-between gap-3 py-2">
                <span>{enums(`attachmentType.${attachment.file_type}`)}</span>
                <span className="text-faint tabular-nums">
                  {t("attachments.size", {
                    size: formatNumber(locale, attachment.size_bytes / 1024, 0),
                  })}
                </span>
                <a
                  href={`/attachments/${injury.id}/${attachment.id}`}
                  className="text-accent font-medium hover:underline"
                >
                  {t("attachments.download")}
                </a>
              </li>
            ))}
          </ul>
        )}
        <AttachmentUpload injuryId={injury.id} />
      </section>
    </Card>
  );
}

export default async function InjuriesPage() {
  const t = await getTranslations("injuries");
  const [profile, injuries, injuryTypes] = await Promise.all([
    getProfile(),
    getInjuries(),
    getInjuryTypes(),
  ]);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-7">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      <SetupGate profile={profile} />

      <Card>
        <CardHeader title={t("add")} />
        <InjuryForm injuryTypes={injuryTypes} today={todayIso()} />
      </Card>

      {injuries.length === 0 ? (
        <p className="text-subtle text-sm">{t("empty")}</p>
      ) : (
        injuries.map((injury) => (
          <InjuryCard key={injury.id} injury={injury} injuryTypes={injuryTypes} />
        ))
      )}
    </div>
  );
}
