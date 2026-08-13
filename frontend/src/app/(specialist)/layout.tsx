import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { Shell } from "@/components/shell";
import { getCurrentUser } from "@/lib/api/queries";
import { homeForRole } from "@/lib/auth/roles";

const LINKS = [
  { href: "/specialist", key: "patients" },
  { href: "/specialist/review", key: "review" },
] as const;

/**
 * مساحة الأخصائي.
 *
 * المدير يُحوَّل للوحته لا لهنا: هذه الشاشات تعرض **مرضى الأخصائي
 * المسنَدين**، ولا يُسنَد للمدير أحد، فكانت ستصله فارغة دائمًا.
 */
export default async function SpecialistLayout({ children }: { children: React.ReactNode }) {
  const [user, nav] = await Promise.all([getCurrentUser(), getTranslations("specialistNav")]);
  if (user.role !== "specialist") redirect(homeForRole(user.role));

  const links = LINKS.map((link) => ({ href: link.href, label: nav(link.key) }));
  return (
    <Shell user={user} links={links}>
      {children}
    </Shell>
  );
}
