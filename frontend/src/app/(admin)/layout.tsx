import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { Shell } from "@/components/shell";
import { getCurrentUser } from "@/lib/api/queries";
import { homeForRole } from "@/lib/auth/roles";

const LINKS = [
  { href: "/admin", key: "overview" },
  { href: "/admin/users", key: "users" },
  { href: "/admin/assignments", key: "assignments" },
] as const;

/**
 * مساحة المدير.
 *
 * الحماية على مستويين كالمساحات الأخرى: `src/proxy.ts` يمنع غير
 * المسجّلين، وهذا التخطيط يمنع الدور الخطأ. الطبقة الثالثة — وهي التي
 * يُعتدّ بها — في الخادم: كل مسار تحت `/admin` يشترط دور المدير، فلا
 * يكفي تجاوز الواجهة.
 */
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const [user, nav] = await Promise.all([getCurrentUser(), getTranslations("adminNav")]);
  if (user.role !== "admin") redirect(homeForRole(user.role));

  const links = LINKS.map((link) => ({ href: link.href, label: nav(link.key) }));
  return (
    <Shell user={user} links={links}>
      {children}
    </Shell>
  );
}
