import { AppShell } from "@/components/app-shell";

/**
 * كل ما تحت هذه المجموعة يتطلب جلسة.
 *
 * الحماية الفعلية في `src/proxy.ts` (اصطلاح Next 16 لما كان اسمه
 * middleware): يعيد التوجيه قبل أي render. وهذا التخطيط يفترض وجود
 * الجلسة ويبني الهيكل حولها.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
