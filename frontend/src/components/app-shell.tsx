import { getTranslations } from "next-intl/server";

import { Link } from "@/components/ui/nav-link";
import { Button } from "@/components/ui/button";
import { logoutAction } from "@/lib/auth/actions";
import { getCurrentUser } from "@/lib/api/queries";

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
  const user = await getCurrentUser();

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-border bg-surface sticky top-0 z-10 border-b">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-5 gap-y-2 px-5 py-3">
          <Link href="/dashboard" className="text-primary font-bold">
            {app("name")}
          </Link>

          <nav aria-label={nav("menu")} className="flex flex-1 flex-wrap gap-x-4 gap-y-1 text-sm">
            {LINKS.map((link) => (
              <Link key={link.href} href={link.href} className="hover:text-primary py-1">
                {nav(link.key)}
              </Link>
            ))}
          </nav>

          <form action={logoutAction}>
            <span className="text-muted me-3 hidden text-xs sm:inline">{user.full_name}</span>
            <Button type="submit" variant="ghost" size="sm">
              {nav("logout")}
            </Button>
          </form>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-8">{children}</main>
    </div>
  );
}
