import { getTranslations } from "next-intl/server";

import { Link } from "@/components/ui/nav-link";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/admin/catalog/foods", key: "foods" },
  { href: "/admin/catalog/exercises", key: "exercises" },
  { href: "/admin/catalog/injuries", key: "injuries" },
] as const;

/** ترويسة القاعدة العلمية — عنوان واحد وثلاثة تبويبات لثلاثة كيانات. */
export async function CatalogHeader({ current }: { current: "foods" | "exercises" | "injuries" }) {
  const t = await getTranslations("admin.catalog");

  return (
    <header className="flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </div>

      <nav className="flex flex-wrap gap-2" aria-label={t("title")}>
        {TABS.map((tab) => (
          <Link
            key={tab.key}
            href={tab.href}
            aria-current={tab.key === current ? "page" : undefined}
            className={cn(
              "cut cut-sm px-3.5 py-2 text-sm whitespace-nowrap transition-colors",
              tab.key === current ? "bg-ink text-paper" : "bg-raised text-subtle hover:text-ink",
            )}
          >
            {t(tab.key)}
          </Link>
        ))}
      </nav>
    </header>
  );
}
