import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Alert, Badge } from "@/components/ui/alert";
import { Card, CardHeader } from "@/components/ui/card";
import { getFoods } from "@/lib/api/admin-queries";
import { FOOD_CATEGORIES, type FoodCategory } from "@/lib/api/schema";
import { formatNumber, toNumber } from "@/lib/format";
import { readLocale } from "@/lib/preferences";
import { CatalogFilters, CONTROL, LABEL } from "../filters";
import { FoodForm } from "../forms";
import { CatalogHeader } from "../tabs";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("admin.catalog");
  return { title: `${t("foods")} — ${t("title")}` };
}

type Search = { search?: string; category?: string; status?: string };

export default async function FoodsPage({ searchParams }: { searchParams: Promise<Search> }) {
  const t = await getTranslations("admin.catalog");
  const enums = await getTranslations("enums");
  const locale = await readLocale();
  const params = await searchParams;

  const category = (FOOD_CATEGORIES as readonly string[]).includes(params.category ?? "")
    ? (params.category as FoodCategory)
    : undefined;
  const search = params.search?.trim() ?? "";
  const isActive =
    params.status === "active" ? true : params.status === "disabled" ? false : undefined;

  const foods = await getFoods({ search: search || undefined, category, isActive });
  const filtered = search !== "" || category !== undefined || isActive !== undefined;

  return (
    <div className="flex flex-col gap-8">
      <CatalogHeader current="foods" />

      <CatalogFilters
        action="/admin/catalog/foods"
        search={search}
        status={params.status ?? ""}
        filtered={filtered}
        extras={
          <label className="flex flex-col gap-1.5">
            <span className={LABEL}>{t("filterCategory")}</span>
            <select name="category" defaultValue={category ?? ""} className={CONTROL}>
              <option value="">{t("all")}</option>
              {FOOD_CATEGORIES.map((value) => (
                <option key={value} value={value}>
                  {enums(`foodCategory.${value}`)}
                </option>
              ))}
            </select>
          </label>
        }
      />

      <Alert tone="info">{t("noDelete")}</Alert>

      {foods.length === 0 ? (
        <Card>
          <CardHeader title={t("empty")} />
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          <p className={LABEL}>{t("count", { count: foods.length })}</p>
          {foods.map((food) => (
            <details
              key={food.id}
              className="border-line bg-surface group rounded-xs border px-5 py-4"
            >
              <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3">
                <span className="flex min-w-0 flex-col">
                  <span className="font-medium">{food.name_ar}</span>
                  <span className="text-subtle text-xs">
                    {enums(`foodCategory.${food.category}`)} ·{" "}
                    {formatNumber(locale, toNumber(food.calories_per_100g) ?? 0, 0)} kcal
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  {!food.is_active && <Badge tone="danger">{t("disabled")}</Badge>}
                  {food.allergens.length > 0 && (
                    <Badge tone="warning">
                      {food.allergens.map((item) => enums(`allergen.${item}`)).join("، ")}
                    </Badge>
                  )}
                  <span className="text-faint text-xs group-open:hidden">{t("edit")}</span>
                </span>
              </summary>
              <div className="pt-5">
                <FoodForm food={food} />
              </div>
            </details>
          ))}
        </div>
      )}

      <Card className="flex flex-col gap-5">
        <CardHeader title={t("addNew")} />
        <FoodForm />
      </Card>
    </div>
  );
}
