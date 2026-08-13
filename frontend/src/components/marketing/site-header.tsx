import { getTranslations } from "next-intl/server";

import { Wordmark } from "@/components/brand";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { buttonStyles } from "@/components/ui/button";
import { Link } from "@/components/ui/nav-link";
import type { Locale, Theme } from "@/i18n/config";
import { getVisitor } from "@/lib/api/queries";
import { homeForRole, workspaceKey } from "@/lib/auth/roles";

const SECTIONS = [
  { href: "#how", key: "how" },
  { href: "#features", key: "features" },
  { href: "#safety", key: "safety" },
  { href: "#faq", key: "faq" },
] as const;

/**
 * الشريط العلوي للصفحة الخارجية.
 *
 * **لوح حبري طافٍ** بزاوية مقصوصة، بعرض المحتوى لا بعرض الشاشة، يفصله
 * هامش عن أعلى الصفحة فيبدو مركّبًا فوقها. البديل الشائع — شريط ممتدّ
 * شبه شفاف مع ضبابية — هو أكثر ما يجعل المواقع متشابهة، ويختفي فوق
 * المحتوى الفاتح.
 *
 * الكتلة الداكنة تحلّ مشكلة أخرى: الصفحة الخارجية فاتحة وطباشيرية، فبقاء
 * الشريط بلونها كان يجعل حدّه السفلي هو الشيء الوحيد الذي يعرّفه.
 *
 * الشريط يعرف الجلسة: الزائر يرى دعوتين للدخول، والمسجَّل يرى اسمه وزرًا
 * يفتح مساحته. الوجهة والتسمية يشتقّان من الدور، فالصفحة الخارجية تصلح
 * بابًا للجميع بلا نسخة لكل دور.
 */
export async function SiteHeader({ locale, theme }: { locale: Locale; theme: Theme }) {
  const [t, auth, app, translate, visitor] = await Promise.all([
    getTranslations("landing.nav"),
    getTranslations("auth"),
    getTranslations("app"),
    getTranslations(),
    getVisitor(),
  ]);

  return (
    <header className="slab-shadow sticky top-0 z-40 px-2 pt-3 pb-2 sm:px-3">
      <div className="cut cut-lg bg-slab text-slab-ink mx-auto flex h-14 max-w-6xl items-center gap-2 ps-3 pe-1.5 sm:gap-6 sm:ps-5 sm:pe-2">
        <Link href="/" className="shrink-0">
          <Wordmark name={app("name")} />
        </Link>

        {/* روابط الأقسام تختفي على الشاشات الصغيرة: التنقّل الحقيقي هناك
            هو التمرير، وازدحام الشريط يدفع زر البدء خارج الشاشة. */}
        <nav className="hidden flex-1 items-center gap-7 text-sm md:flex">
          {SECTIONS.map((section) => (
            <a
              key={section.href}
              href={section.href}
              className="after:bg-signal relative py-1 opacity-70 transition-opacity after:absolute after:inset-x-0 after:-bottom-0.5 after:h-0.5 after:opacity-0 after:transition-opacity hover:opacity-100 hover:after:opacity-100"
            >
              {t(section.key)}
            </a>
          ))}
        </nav>

        <div className="ms-auto flex items-center gap-1.5 sm:gap-2 md:ms-0">
          <LocaleSwitcher current={locale} />
          <ThemeToggle initial={theme} />

          {visitor === null ? (
            <>
              <Link href="/login" className={buttonStyles({ variant: "ghost", size: "sm" })}>
                {auth("login")}
              </Link>
              {/* زر التسجيل يختفي تحت `sm`: الخمسة عناصر معًا تتجاوز عرض
                  390px فتُدفع خارج الشاشة ويظهر تمرير أفقي. البديل حاضر في
                  نفس الشاشة — النداء الرئيسي في البطل تحته مباشرة.

                  `max-sm:hidden` لا `hidden sm:inline-flex`: الأخيرة تتصادم
                  مع `inline-flex` في أساس الزر، وترتيب الملف الناتج هو ما
                  يحسم التصادم لا ترتيب الفئات هنا. */}
              <Link
                href="/register"
                className={buttonStyles({
                  variant: "signal",
                  size: "sm",
                  className: "max-sm:hidden",
                })}
              >
                {auth("register")}
              </Link>
            </>
          ) : (
            <>
              <span className="me-1 hidden text-xs font-medium lg:block">{visitor.full_name}</span>
              <Link
                href={homeForRole(visitor.role)}
                className={buttonStyles({ variant: "signal", size: "sm" })}
              >
                {translate(workspaceKey(visitor.role))}
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
