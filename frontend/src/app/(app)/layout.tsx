import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { Shell } from "@/components/shell";
import { getCurrentUser } from "@/lib/api/queries";
import { homeForRole } from "@/lib/auth/roles";

const LINKS = [
  { href: "/dashboard", key: "dashboard" },
  { href: "/plan", key: "plan" },
  { href: "/log", key: "log" },
  { href: "/injuries", key: "injuries" },
  { href: "/profile", key: "profile" },
] as const;

/**
 * مساحة المريض.
 *
 * الحماية على مستويين: `src/proxy.ts` يمنع غير المسجّلين قبل أي render،
 * وهذا التخطيط يمنع **الدور الخطأ** — أخصائي يفتح `/dashboard` يُحوَّل
 * لمساحته بدل أن يرى شاشة تطلب منه استكمال ملف مريض.
 */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const [user, nav] = await Promise.all([getCurrentUser(), getTranslations("nav")]);
  if (user.role !== "patient") redirect(homeForRole(user.role));

  const links = LINKS.map((link) => ({ href: link.href, label: nav(link.key) }));
  return (
    <Shell user={user} links={links} home="/dashboard">
      {children}
    </Shell>
  );
}
