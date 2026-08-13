import "server-only";

import { cache } from "react";

import { apiFetch } from "./server";
import type { AdminUserRow, PlatformStats, UserRole } from "./schema";

/**
 * قراءات لوحة المدير.
 *
 * التصفية تحدث في الخادم لا في المتصفح: قائمة المستخدمين تكبر مع المنصة،
 * وجلبها كاملة لتصفيتها في الواجهة يعني تحميل كل الحسابات لعرض عشرة.
 */

export type UserFilters = {
  role?: UserRole;
  search?: string;
  isActive?: boolean;
};

function queryOf(filters: UserFilters): string {
  const params = new URLSearchParams();
  if (filters.role !== undefined) params.set("role", filters.role);
  if (filters.search) params.set("search", filters.search);
  if (filters.isActive !== undefined) params.set("is_active", String(filters.isActive));
  params.set("limit", "200");
  return params.toString();
}

export const getAdminUsers = cache(async (filters: UserFilters = {}): Promise<AdminUserRow[]> => {
  return apiFetch<AdminUserRow[]>(`/admin/users?${queryOf(filters)}`);
});

export const getPlatformStats = cache(async (): Promise<PlatformStats> => {
  return apiFetch<PlatformStats>("/admin/stats");
});
