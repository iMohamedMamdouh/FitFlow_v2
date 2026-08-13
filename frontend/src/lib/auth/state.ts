/**
 * حالة نماذج المصادقة.
 *
 * منفصلة عن ملف الـ actions لأن ملفًا يحمل `"use server"` لا يُصدِّر إلا
 * دوالًا غير متزامنة — أي ثابت أو نوع فيه يكسر البناء.
 */
export type AuthState = { error: string | null };

export const EMPTY_AUTH_STATE: AuthState = { error: null };
