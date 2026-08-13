import { getTranslations } from "next-intl/server";

import { buttonStyles } from "@/components/ui/button";
import { Link } from "@/components/ui/nav-link";

const CONTROL =
  "border-line border-b-line-strong bg-raised text-ink placeholder:text-faint " +
  "rounded-xs border border-b-2 px-3.5 py-2.5 text-sm";

const LABEL = "text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase";

/**
 * شريط التصفية.
 *
 * نموذج `GET` عادي: المعايير تصبح في الرابط فيمكن حفظه ومشاركته والعودة
 * إليه بعد أي فعل — وهو بالضبط ما يضيع لو عاشت الحالة في المتصفح.
 *
 * الخيارات تُمرَّر من الصفحة لأنها تختلف بين الكيانات: تصنيف طعام ليس
 * منطقة جسم، ونموذج واحد بكل الخيارات يعرض حقولًا لا معنى لها.
 */
export async function CatalogFilters({
  action,
  search,
  status,
  extras,
  showUnreviewed = false,
  unreviewed,
  filtered,
}: {
  action: string;
  search: string;
  status: string;
  extras?: React.ReactNode;
  showUnreviewed?: boolean;
  unreviewed?: boolean;
  filtered: boolean;
}) {
  const t = await getTranslations("admin.catalog");

  return (
    <form className="border-line bg-surface flex flex-wrap items-end gap-4 rounded-xs border p-5">
      <label className="flex min-w-52 flex-1 flex-col gap-1.5">
        <span className={LABEL}>{t("search")}</span>
        <input
          type="search"
          name="search"
          defaultValue={search}
          placeholder={t("searchPlaceholder")}
          className={CONTROL}
        />
      </label>

      {extras}

      <label className="flex flex-col gap-1.5">
        <span className={LABEL}>{t("filterStatus")}</span>
        <select name="status" defaultValue={status} className={CONTROL}>
          <option value="">{t("all")}</option>
          <option value="active">{t("onlyActive")}</option>
          <option value="disabled">{t("onlyDisabled")}</option>
        </select>
      </label>

      {showUnreviewed && (
        <label className="flex items-center gap-2 py-2.5 text-sm">
          <input
            type="checkbox"
            name="unreviewed"
            value="true"
            defaultChecked={unreviewed}
            className="accent-accent size-4"
          />
          {t("onlyUnreviewed")}
        </label>
      )}

      <div className="flex gap-2">
        <button type="submit" className={buttonStyles({ size: "md" })}>
          {t("apply")}
        </button>
        {filtered && (
          <Link href={action} className={buttonStyles({ variant: "quiet", size: "md" })}>
            {t("reset")}
          </Link>
        )}
      </div>
    </form>
  );
}

export { CONTROL, LABEL };
