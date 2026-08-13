import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { Shell } from "@/components/shell";
import { getCurrentUser } from "@/lib/api/queries";
import { homeForRole, isCareTeam } from "@/lib/auth/roles";

const LINKS = [
  { href: "/specialist", key: "patients" },
  { href: "/specialist/review", key: "review" },
] as const;

/** مساحة الأخصائي والمدير — المريض يُحوَّل لمساحته. */
export default async function SpecialistLayout({ children }: { children: React.ReactNode }) {
  const [user, nav] = await Promise.all([getCurrentUser(), getTranslations("specialistNav")]);
  if (!isCareTeam(user.role)) redirect(homeForRole(user.role));

  const links = LINKS.map((link) => ({ href: link.href, label: nav(link.key) }));
  return (
    <Shell user={user} links={links} home="/specialist">
      {children}
    </Shell>
  );
}
