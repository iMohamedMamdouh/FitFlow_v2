import { getTranslations } from "next-intl/server";

import { Wordmark } from "@/components/brand";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Link } from "@/components/ui/nav-link";
import { logoutAction } from "@/lib/auth/actions";
import { getCurrentUser } from "@/lib/api/queries";
import { readLocale, readTheme } from "@/lib/preferences";

const LINKS = [
  { href: "/dashboard", key: "dashboard" },
  { href: "/plan", key: "plan" },
  { href: "/log", key: "log" },
  { href: "/injuries", key: "injuries" },
  { href: "/profile", key: "profile" },
] as const;

export async function AppShell({ children }: { children: React.ReactNode }) {
  const nav = await getTranslations("nav");
  const app = await getTranslations("app");
  const [user, locale, theme] = await Promise.all([getCurrentUser(), readLocale(), readTheme()]);

  const initials = user.full_name.trim().charAt(0).toUpperCase();

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-line bg-paper/85 sticky top-0 z-40 border-b backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-5">
          <Link href="/dashboard" className="shrink-0">
            <Wordmark name={app("name")} />
          </Link>

          <div className="ms-auto flex items-center gap-2">
            <LocaleSwitcher current={locale} />
            <ThemeToggle initial={theme} />

            <form action={logoutAction} className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="bg-accent-wash text-accent font-display hidden size-8 items-center justify-center rounded-full text-sm font-semibold sm:flex"
              >
                {initials}
              </span>
              <span className="text-subtle me-1 hidden text-xs lg:inline">{user.full_name}</span>
              <Button type="submit" variant="quiet" size="sm">
                {nav("logout")}
              </Button>
            </form>
          </div>
        </div>

        {/* التنقّل في شريط ثانٍ قابل للتمرير أفقيًا: خمسة روابط + أدوات
            العرض لا تتسع في شريط واحد على الموبايل، والطيّ خلف زر قائمة
            يخفي المسارات الخمسة التي يستخدمها المريض يوميًا. */}
        <nav
          aria-label={nav("menu")}
          className="border-line/60 mx-auto flex max-w-6xl gap-1 overflow-x-auto border-t px-3 text-sm"
        >
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-subtle hover:text-ink hover:border-accent border-b-2 border-transparent px-3 py-2.5 whitespace-nowrap transition-colors"
            >
              {nav(link.key)}
            </Link>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-10">{children}</main>

      <footer className="border-line text-faint border-t px-5 py-6 text-center text-xs">
        {app("name")} — {app("tagline")}
      </footer>
    </div>
  );
}
