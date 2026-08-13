import type { UserRole } from "@/lib/api/schema";

/**
 * الصفحة الرئيسية لكل دور.
 *
 * الأدوار لا تتشارك شاشة بداية: المريض يبدأ من لوحته، والأخصائي من قائمة
 * مرضاه، والمدير من لوحته. توجيه الجميع إلى `/dashboard` يعني أن أخصائيًا
 * يفتح شاشة تطلب منه "استكمال ملفه الشخصي" — وهو ليس مريضًا أصلًا، ويعني
 * أن مديرًا يهبط على قائمة مرضى فارغة لأنه لا يُسنَد إليه أحد.
 */
export function homeForRole(role: UserRole): string {
  if (role === "patient") return "/dashboard";
  return role === "admin" ? "/admin" : "/specialist";
}

/**
 * مفتاح تسمية مساحة الدور.
 *
 * "لوحتي" في زرّ يفتح قائمة مرضى تسمية خاطئة، فالتسمية تتبع الوجهة لا
 * العكس — والوجهة نفسها تأتي من `homeForRole`.
 */
export function workspaceKey(
  role: UserRole,
): "nav.dashboard" | "specialistNav.patients" | "adminNav.overview" {
  if (role === "patient") return "nav.dashboard";
  return role === "admin" ? "adminNav.overview" : "specialistNav.patients";
}
