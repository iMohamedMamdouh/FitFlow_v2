/**
 * حالة نماذج شاشة المستخدمين.
 *
 * في ملف مستقل لأن ملفات `"use server"` لا تصدّر إلا دوالّ غير متزامنة.
 */
export type AdminActionState = { error: string | null; message: string | null };

export const EMPTY_ADMIN_STATE: AdminActionState = { error: null, message: null };
