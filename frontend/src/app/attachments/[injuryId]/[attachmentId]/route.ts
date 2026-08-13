import { NextResponse } from "next/server";

import { ApiError } from "@/lib/api/errors";
import { apiFetchBlob } from "@/lib/api/server";

/**
 * تنزيل مرفق طبي.
 *
 * المسار الوحيد في الواجهة الذي يخدم بايتات. هو موجود لأن المتصفح لا
 * يملك رمز الوصول (الجلسة في كوكي `httpOnly`)، فلا يستطيع نداء الـ API
 * مباشرة؛ هذا المسار يقرأ الكوكي على الخادم ويمرّر الطلب.
 *
 * لا يضيف أي صلاحية: التحقق من ملكية الإصابة يحدث في الخادم، ورد 404
 * منه يصل كما هو.
 */
export async function GET(
  _request: Request,
  context: { params: Promise<{ injuryId: string; attachmentId: string }> },
): Promise<NextResponse> {
  const { injuryId, attachmentId } = await context.params;

  try {
    const file = await apiFetchBlob(`/me/injuries/${injuryId}/attachments/${attachmentId}/content`);
    return new NextResponse(file.body, {
      headers: {
        "Content-Type": file.type,
        // تنزيل لا عرض داخل النطاق — ملف رفعه مستخدم لا يُنفَّذ في صفحتنا.
        "Content-Disposition": `attachment; filename="${attachmentId}"`,
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    const status = error instanceof ApiError ? (error.status === 0 ? 502 : error.status) : 500;
    return NextResponse.json({ error: true }, { status });
  }
}
