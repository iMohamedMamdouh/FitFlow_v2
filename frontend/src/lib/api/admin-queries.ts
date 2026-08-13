import "server-only";

import { cache } from "react";

import { apiFetch } from "./server";
import type {
  AdminUserRow,
  BodyRegion,
  ExerciseCategory,
  ExerciseRow,
  FoodCategory,
  FoodRow,
  InjuryTypeRow,
  PlatformStats,
  UserRole,
} from "./schema";

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

/**
 * قراءات القاعدة العلمية.
 *
 * التصفية في الخادم كذلك: قائمة الأغذية وحدها بالمئات، وجلبها كاملة
 * لتصفيتها في المتصفح يعني تحميل القاعدة كلها لعرض صفحة.
 */
export type CatalogFilters = {
  search?: string;
  isActive?: boolean;
  category?: string;
  region?: BodyRegion;
  unreviewed?: boolean;
};

function catalogQuery(filters: CatalogFilters): string {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.isActive !== undefined) params.set("is_active", String(filters.isActive));
  if (filters.category) params.set("category", filters.category);
  if (filters.region) params.set("region", filters.region);
  if (filters.unreviewed) params.set("unreviewed", "true");
  params.set("limit", "300");
  return params.toString();
}

export const getFoods = cache(async (filters: CatalogFilters = {}): Promise<FoodRow[]> => {
  return apiFetch<FoodRow[]>(`/admin/catalog/foods?${catalogQuery(filters)}`);
});

export const getExercises = cache(async (filters: CatalogFilters = {}): Promise<ExerciseRow[]> => {
  return apiFetch<ExerciseRow[]>(`/admin/catalog/exercises?${catalogQuery(filters)}`);
});

export const getInjuryTypes = cache(
  async (filters: CatalogFilters = {}): Promise<InjuryTypeRow[]> => {
    return apiFetch<InjuryTypeRow[]>(`/admin/catalog/injury-types?${catalogQuery(filters)}`);
  },
);

export type { ExerciseCategory, FoodCategory };
