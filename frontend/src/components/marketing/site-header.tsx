import { getTranslations } from "next-intl/server";

import { Wordmark } from "@/components/brand";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { buttonStyles } from "@/components/ui/button";
import { Link } from "@/components/ui/nav-link";
import type { Locale, Theme } from "@/i18n/config";

const SECTIONS = [
  { href: "#how", key: "how" },
  { href: "#features", key: "features" },
  { href: "#safety", key: "safety" },
  { href: "#faq", key: "faq" },
] as const;

export async function SiteHeader({ locale, theme }: { locale: Locale; theme: Theme }) {
  const t = await getTranslations("landing.nav");
  const auth = await getTranslations("auth");
  const app = await getTranslations("app");

  return (
    <header className="border-line bg-paper/85 sticky top-0 z-40 border-b backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-5">
        <Link href="/" className="shrink-0">
          <Wordmark name={app("name")} />
        </Link>

        {/* روابط الأقسام تختفي على الشاشات الصغيرة: التنقّل الحقيقي هناك
            هو التمرير، وازدحام الشريط يدفع زر البدء خارج الشاشة. */}
        <nav className="text-subtle hidden flex-1 items-center gap-7 text-sm md:flex">
          {SECTIONS.map((section) => (
            <a key={section.href} href={section.href} className="hover:text-ink transition-colors">
              {t(section.key)}
            </a>
          ))}
        </nav>

        {/* زر التسجيل يختفي تحت `sm`: الخمسة عناصر معًا تتجاوز عرض 390px
            فتُدفع خارج الشاشة ويظهر تمرير أفقي. البديل حاضر في نفس الشاشة
            — النداء الرئيسي في البطل تحته مباشرة. */}
        <div className="ms-auto flex items-center gap-1.5 sm:gap-2 md:ms-0">
          <LocaleSwitcher current={locale} />
          <ThemeToggle initial={theme} />
          <Link href="/login" className={buttonStyles({ variant: "quiet", size: "sm" })}>
            {auth("login")}
          </Link>
          <Link
            href="/register"
            className={buttonStyles({
              variant: "clay",
              size: "sm",
              className: "hidden sm:inline-flex",
            })}
          >
            {auth("register")}
          </Link>
        </div>
      </div>
    </header>
  );
}
