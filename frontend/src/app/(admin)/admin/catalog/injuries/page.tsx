import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Alert, Badge } from "@/components/ui/alert";
import { Card, CardHeader } from "@/components/ui/card";
import { getInjuryTypes } from "@/lib/api/admin-queries";
import { BODY_REGIONS, type BodyRegion } from "@/lib/api/schema";
import { formatDate } from "@/lib/format";
import { readLocale } from "@/lib/preferences";
import { CatalogFilters, CONTROL, LABEL } from "../filters";
import { InjuryTypeForm, ReviewForm } from "../forms";
import { CatalogHeader } from "../tabs";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("admin.catalog");
  return { title: `${t("injuries")} — ${t("title")}` };
}

type Search = { search?: string; region?: string; status?: string; unreviewed?: string };

export default async function InjuryTypesPage({ searchParams }: { searchParams: Promise<Search> }) {
  const t = await getTranslations("admin.catalog");
  const enums = await getTranslations("enums");
  const locale = await readLocale();
  const params = await searchParams;

  const region = (BODY_REGIONS as readonly string[]).includes(params.region ?? "")
    ? (params.region as BodyRegion)
    : undefined;
  const search = params.search?.trim() ?? "";
  const isActive =
    params.status === "active" ? true : params.status === "disabled" ? false : undefined;
  const unreviewed = params.unreviewed === "true";

  const injuryTypes = await getInjuryTypes({
    search: search || undefined,
    region,
    isActive,
    unreviewed,
  });
  const filtered = search !== "" || region !== undefined || isActive !== undefined || unreviewed;

  return (
    <div className="flex flex-col gap-8">
      <CatalogHeader current="injuries" />

      <CatalogFilters
        action="/admin/catalog/injuries"
        search={search}
        status={params.status ?? ""}
        filtered={filtered}
        showUnreviewed
        unreviewed={unreviewed}
        extras={
          <label className="flex flex-col gap-1.5">
            <span className={LABEL}>{t("filterRegion")}</span>
            <select name="region" defaultValue={region ?? ""} className={CONTROL}>
              <option value="">{t("all")}</option>
              {BODY_REGIONS.map((value) => (
                <option key={value} value={value}>
                  {enums(`bodyRegion.${value}`)}
                </option>
              ))}
            </select>
          </label>
        }
      />

      <Alert tone="info">{t("noDelete")}</Alert>

      {injuryTypes.length === 0 ? (
        <Card>
          <CardHeader title={t("empty")} />
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          <p className={LABEL}>{t("count", { count: injuryTypes.length })}</p>
          {injuryTypes.map((injuryType) => (
            <details
              key={injuryType.id}
              className="border-line bg-surface group rounded-xs border px-5 py-4"
            >
              <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3">
                <span className="flex min-w-0 flex-col">
                  <span className="font-medium">{injuryType.name_ar}</span>
                  <span className="text-subtle text-xs">
                    {enums(`bodyRegion.${injuryType.body_region}`)} · {injuryType.phases.length}{" "}
                    {t("phases")}
                  </span>
                </span>
                <span className="flex flex-wrap items-center gap-2">
                  {!injuryType.is_active && <Badge tone="danger">{t("disabled")}</Badge>}
                  <Badge tone={injuryType.review.is_reviewed ? "success" : "warning"}>
                    {injuryType.review.is_reviewed ? t("reviewed") : t("unreviewed")}
                  </Badge>
                  <Badge tone="neutral">
                    {t("version", { version: injuryType.review.content_version })}
                  </Badge>
                  <span className="text-faint text-xs group-open:hidden">{t("edit")}</span>
                </span>
              </summary>

              <div className="flex flex-col gap-5 pt-5">
                {injuryType.review.reviewed_at !== null && (
                  <p className="text-subtle text-xs leading-6">
                    {t("reviewedAt", { date: formatDate(locale, injuryType.review.reviewed_at) })} —{" "}
                    {injuryType.review.reviewed_by} · {injuryType.review.source_reference}
                  </p>
                )}
                <InjuryTypeForm injuryType={injuryType} />
                <ReviewForm kind="injury-types" id={injuryType.id} review={injuryType.review} />
              </div>
            </details>
          ))}
        </div>
      )}

      <Card className="flex flex-col gap-5">
        <CardHeader title={t("addNew")} description={t("versionHint")} />
        <InjuryTypeForm />
      </Card>
    </div>
  );
}
