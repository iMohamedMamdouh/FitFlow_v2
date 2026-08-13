import { getTranslations } from "next-intl/server";

import { Wordmark } from "@/components/brand";
import { Link } from "@/components/ui/nav-link";

export async function SiteFooter() {
  const app = await getTranslations("app");
  const t = await getTranslations("landing.footer");
  const nav = await getTranslations("landing.nav");
  const auth = await getTranslations("auth");

  return (
    <footer>
      <div aria-hidden="true" className="tick-rule" />
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <Wordmark name={app("name")} tagline={app("tagline")} />
          <p className="text-subtle mt-4 max-w-sm text-sm leading-7">{t("tagline")}</p>
        </div>

        <div>
          <h3 className="text-faint text-[0.7rem] font-semibold tracking-[0.14em] uppercase">
            {t("product")}
          </h3>
          <ul className="text-subtle mt-4 flex flex-col gap-2.5 text-sm">
            <li>
              <a href="#how" className="hover:text-ink transition-colors">
                {nav("how")}
              </a>
            </li>
            <li>
              <a href="#features" className="hover:text-ink transition-colors">
                {nav("features")}
              </a>
            </li>
            <li>
              <a href="#safety" className="hover:text-ink transition-colors">
                {nav("safety")}
              </a>
            </li>
            <li>
              <Link href="/login" className="hover:text-ink transition-colors">
                {auth("login")}
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-faint text-[0.7rem] font-semibold tracking-[0.14em] uppercase">
            {t("disclaimerTitle")}
          </h3>
          {/* التنبيه في التذييل لا في صفحة منفصلة: تحذير خلف رابط لا يُقرأ. */}
          <p className="text-subtle mt-4 text-xs leading-6">{t("disclaimer")}</p>
        </div>
      </div>

      <div className="border-line text-faint border-t px-5 py-6 text-center text-xs">
        © {new Date().getFullYear()} {app("name")} — {t("rights")}
      </div>
    </footer>
  );
}
