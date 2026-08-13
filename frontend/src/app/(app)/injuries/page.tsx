import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { SetupGate } from "@/components/setup-gate";
import { Alert, Badge } from "@/components/ui/alert";
import { Card, CardHeader } from "@/components/ui/card";
import { apiFetch } from "@/lib/api/server";
import { getInjuries, getInjuryTypes, getProfile } from "@/lib/api/queries";
import { formatDate, formatNumber, todayIso } from "@/lib/format";
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

  const injuryType = typeOf(injury, injuryTypes);
  const attachments = await apiFetch<AttachmentRead[]>(`/me/injuries/${injury.id}/attachments`);

  return (
    <Card>
      <CardHeader
        title={injuryType?.name_ar ?? common("unknown")}
        description={`${formatDate(injury.injury_date)} • ${t("phase", { phase: injury.current_phase })}`}
        action={
          <Badge tone={injury.status === "acute" ? "danger" : "neutral"}>
            {enums(`injuryStatus.${injury.status}`)}
          </Badge>
        }
      />

      <dl className="grid gap-2 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted">{t("pain")}</dt>
          <dd className="tabular-nums">{injury.pain_level}/10</dd>
        </div>
        <div>
          <dt className="text-muted">{t("side")}</dt>
          <dd>{enums(`bodySide.${injury.side}`)}</dd>
        </div>
        <div>
          <dt className="text-muted">{t("hadSurgery")}</dt>
          <dd>{injury.had_surgery ? formatDate(injury.surgery_date) : common("no")}</dd>
        </div>
      </dl>

      {injury.notes !== null && injury.notes !== "" && (
        <p className="text-muted mt-3 text-sm leading-7">{injury.notes}</p>
      )}

      {injury.status === "acute" && (
        <Alert tone="warning" className="mt-4">
          {t("acuteWarning")}
        </Alert>
      )}

      <section className="border-border mt-5 border-t pt-4">
        <h3 className="text-sm font-semibold">{t("attachments.title")}</h3>
        {attachments.length === 0 ? (
          <p className="text-muted mt-2 text-sm">{t("attachments.empty")}</p>
        ) : (
          <ul className="mt-2 flex flex-col divide-y divide-[var(--color-border)] text-sm">
            {attachments.map((attachment) => (
              <li key={attachment.id} className="flex items-center justify-between gap-3 py-2">
                <span>{enums(`attachmentType.${attachment.file_type}`)}</span>
                <span className="text-muted tabular-nums">
                  {t("attachments.size", {
                    size: formatNumber(attachment.size_bytes / 1024, 0),
                  })}
                </span>
                <a
                  href={`/attachments/${injury.id}/${attachment.id}`}
                  className="text-primary font-medium"
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
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-bold">{t("title")}</h1>
        <p className="text-muted text-sm leading-7">{t("subtitle")}</p>
      </header>

      <SetupGate profile={profile} />

      <Card>
        <CardHeader title={t("add")} />
        <InjuryForm injuryTypes={injuryTypes} today={todayIso()} />
      </Card>

      {injuries.length === 0 ? (
        <p className="text-muted text-sm">{t("empty")}</p>
      ) : (
        injuries.map((injury) => (
          <InjuryCard key={injury.id} injury={injury} injuryTypes={injuryTypes} />
        ))
      )}
    </div>
  );
}
