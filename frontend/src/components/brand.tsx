import { cn } from "@/lib/utils";

/**
 * علامة FitFlow.
 *
 * حرف **F** بضربات سميكة ذات نهايات مستديرة، يقطعه نبض قلب ليموني يخرج
 * من ذراعه الأوسط ويكمل إلى اليمين. القراءتان مقصودتان: الحرف هوية،
 * والنبض هو ما تقيسه المنصة فعلًا.
 *
 * الحرف مرسوم بـ`currentColor` والنبض بلون الإشارة: العلامة توضع على
 * اللوح الحبري الداكن وعلى الورق الفاتح معًا، فتتبع لون النص في الحالتين
 * بلا نسخة ثانية من الملف، بينما يبقى النبض ليمونيًا في الوضعين.
 */
export function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      className={cn("size-7 sm:size-8", className)}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M37 8H18a4.5 4.5 0 0 0-4.5 4.5V40" stroke="currentColor" strokeWidth="6.2" />
      <path d="M13.5 25.5h9" stroke="currentColor" strokeWidth="6.2" />
      <path
        d="M21.5 25.5h3.2l3.4-9.2L32.4 33l2.4-7.5h6.2"
        stroke="var(--color-signal)"
        strokeWidth="5.6"
      />
    </svg>
  );
}

export function Wordmark({
  name,
  tagline,
  className,
}: {
  name: string;
  tagline?: string;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <Logo />
      <span className="flex flex-col leading-none">
        <span className="font-display text-base font-semibold tracking-tight sm:text-lg">
          {name}
        </span>
        {tagline !== undefined && (
          <span className="mt-1 text-[0.65rem] font-medium tracking-wide opacity-60">
            {tagline}
          </span>
        )}
      </span>
    </span>
  );
}
