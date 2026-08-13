import { getTranslations } from "next-intl/server";

import { Wordmark } from "@/components/brand";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { Link } from "@/components/ui/nav-link";
import { readLocale, readTheme } from "@/lib/preferences";

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  const app = await getTranslations("app");
  const auth = await getTranslations("auth");
  const consent = await getTranslations("consent");
  const [locale, theme] = await Promise.all([readLocale(), readTheme()]);

  return (
    <div className="relative flex min-h-dvh flex-col">
      <div
        aria-hidden="true"
        className="bg-lanes pointer-events-none absolute inset-0 [mask-image:radial-gradient(60%_50%_at_50%_0%,black,transparent)]"
      />

      <header className="relative mx-auto flex w-full max-w-6xl items-center gap-3 px-5 py-5">
        <Link href="/">
          <Wordmark name={app("name")} />
        </Link>
        <div className="ms-auto flex items-center gap-2">
          <LocaleSwitcher current={locale} />
          <ThemeToggle initial={theme} />
        </div>
      </header>

      <main className="relative mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-5 px-5 pb-16">
        {children}
        <p className="text-faint text-center text-xs leading-6">{consent("shortNotice")}</p>
        <Link href="/" className="text-subtle hover:text-ink text-center text-xs transition-colors">
          ← {auth("backHome")}
        </Link>
      </main>
    </div>
  );
}
