import { cn } from "@/lib/utils";

/**
 * علامة FitFlow.
 *
 * الرمز أربعة أعمدة متدرّجة الارتفاع داخل مربّع حادّ الزوايا — قراءة
 * مزدوجة مقصودة: قراءات قياس متتابعة، ومنحنى تقدّم صاعد. العمود الأخير
 * وحده بلون الإشارة، فيقرأ كـ"القياس التالي" لا كزينة.
 *
 * العلامة مرسومة بـ`currentColor` عدا عمود الإشارة، فتتبع لون النص
 * أينما وُضعت — على الورق الفاتح أو على اللوح الحبري — بلا نسخة ثانية.
 */
export function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 28 28"
      className={cn("size-6 sm:size-7", className)}
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M1 1h20l6 6v20H1V1Z" fill="currentColor" opacity="0.1" />
      <path
        d="M1 1h20l6 6v20H1V1Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
        opacity="0.5"
      />
      <rect x="6" y="16" width="2.6" height="6" fill="currentColor" />
      <rect x="10.6" y="12.5" width="2.6" height="9.5" fill="currentColor" />
      <rect x="15.2" y="14" width="2.6" height="8" fill="currentColor" />
      <rect x="19.8" y="7" width="2.6" height="15" fill="var(--color-signal)" />
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
