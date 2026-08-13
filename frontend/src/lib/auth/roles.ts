import type { UserRole } from "@/lib/api/schema";

/**
 * الصفحة الرئيسية لكل دور.
 *
 * الأدوار لا تتشارك شاشة بداية: المريض يبدأ من لوحته، والأخصائي والمدير
 * من قائمة المرضى. توجيه الجميع إلى `/dashboard` يعني أن أخصائيًا يفتح
 * شاشة تطلب منه "استكمال ملفه الشخصي" — وهو ليس مريضًا أصلًا.
 */
export function homeForRole(role: UserRole): string {
  return role === "patient" ? "/dashboard" : "/specialist";
}

export function isCareTeam(role: UserRole): boolean {
  return role === "specialist" || role === "admin";
}

/**
 * مفتاح تسمية مساحة الدور.
 *
 * "لوحتي" في زرّ يفتح قائمة مرضى تسمية خاطئة، فالتسمية تتبع الوجهة لا
 * العكس — والوجهة نفسها تأتي من `homeForRole`.
 */
export function workspaceKey(role: UserRole): "nav.dashboard" | "specialistNav.patients" {
  return role === "patient" ? "nav.dashboard" : "specialistNav.patients";
}
