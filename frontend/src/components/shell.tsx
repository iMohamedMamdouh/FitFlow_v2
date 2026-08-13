import { getTranslations } from "next-intl/server";

import { NavRail, NavStrip, type NavLink } from "@/components/app-nav";
import { Wordmark } from "@/components/brand";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Link } from "@/components/ui/nav-link";
import { logoutAction } from "@/lib/auth/actions";
import { readLocale, readTheme } from "@/lib/preferences";
import type { UserPublic } from "@/lib/api/schema";

export type { NavLink };

/**
 * هيكل التطبيق بعد الدخول.
 *
 * الرأسية **لوح حبري طافٍ** لا شريط ممتدّ بعرض الشاشة: كتلة داكنة
 * مقصوصة الزاوية تعلو الصفحة بهامش من ثلاث جهات، فتُقرأ كأداة فوق
 * المحتوى لا كإطار حوله. اللوح يحمل الهوية وأدوات الحساب فقط.
 *
 * التنقّل خرج من الرأسية إلى **مسار جانبي** على الشاشات العريضة: قائمة
 * رأسية تحتمل النموّ (المرحلة العاشرة تضيف مساحة إدارة) بينما الشريط
 * الأفقي كان سيضيق بعد رابطين. تحت `lg` يعود شريط شرائح أفقيًا.
 *
 * المكوّن نفسه للمريض وللأخصائي، ويختلفان في قائمة الروابط فقط: نسخة
 * ثانية من الهيكل لكل دور تعني تعديلين لكل تغيير في التنقّل، وأحدهما
 * يُنسى.
 */
export async function Shell({
  user,
  links,
  home,
  children,
}: {
  user: UserPublic;
  links: readonly NavLink[];
  home: string;
  children: React.ReactNode;
}) {
  const nav = await getTranslations("nav");
  const app = await getTranslations("app");
  const roles = await getTranslations("roles");
  const [locale, theme] = await Promise.all([readLocale(), readTheme()]);

  const initials = user.full_name.trim().charAt(0).toUpperCase();

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="slab-shadow sticky top-0 z-40 px-2 pt-3 pb-2 sm:px-3">
        <div className="cut cut-lg bg-slab text-slab-ink mx-auto flex h-14 max-w-7xl items-center gap-2 ps-3 pe-1.5 sm:gap-3 sm:ps-5 sm:pe-2">
          <Link href={home} className="shrink-0">
            <Wordmark name={app("name")} />
          </Link>

          <div className="ms-auto flex items-center gap-1.5 sm:gap-2">
            <LocaleSwitcher current={locale} />
            <ThemeToggle initial={theme} />

            <form action={logoutAction} className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="bg-signal text-signal-ink font-display hidden size-8 items-center justify-center rounded-xs text-sm font-semibold sm:flex"
              >
                {initials}
              </span>
              <span className="me-1 hidden flex-col leading-tight lg:flex">
                <span className="text-xs font-medium">{user.full_name}</span>
                {/* الدور ظاهر دائمًا: من يملك حسابين — مريضًا وأخصائيًا —
                    يحتاج أن يعرف بأيّهما هو داخل الآن. */}
                <span className="text-[0.65rem] opacity-60">{roles(user.role)}</span>
              </span>
              <Button type="submit" variant="ghost" size="sm">
                {nav("logout")}
              </Button>
            </form>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-8 px-3 sm:px-5">
        <NavRail links={links} label={nav("menu")} />

        <div className="flex min-w-0 flex-1 flex-col">
          <NavStrip links={links} label={nav("menu")} />
          <main className="flex-1 pt-2 pb-12 lg:pt-8">{children}</main>
        </div>
      </div>

      <footer className="mx-auto w-full max-w-7xl px-3 pb-8 sm:px-5">
        <div aria-hidden="true" className="tick-rule" />
        <p className="text-faint pt-4 text-center text-xs">
          {app("name")} — {app("tagline")}
        </p>
      </footer>
    </div>
  );
}
