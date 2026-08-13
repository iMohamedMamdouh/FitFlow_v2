import { cn } from "@/lib/utils";

/**
 * علامة FitFlow.
 *
 * الرمز موجتان صاعدتان داخل مربّع — قراءتان مقصودتان: منحنى تقدّم، وحركة
 * إعادة تأهيل. مرسوم بـ `currentColor` فيتبع لون النص في الوضعين بلا
 * نسختين من الملف.
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
      <rect x="1" y="1" width="26" height="26" rx="8" fill="currentColor" opacity="0.12" />
      <rect
        x="1"
        y="1"
        width="26"
        height="26"
        rx="8"
        stroke="currentColor"
        strokeWidth="1.5"
        opacity="0.45"
      />
      <path
        d="M6 18.5c2.6 0 3.4-6 6-6s3.4 6 6 6 3.4-4 4-4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="18" cy="18.5" r="1.6" fill="currentColor" />
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
      <Logo className="text-accent" />
      <span className="flex flex-col leading-none">
        <span className="font-display text-base font-semibold tracking-tight sm:text-lg">
          {name}
        </span>
        {tagline !== undefined && (
          <span className="text-faint mt-1 text-[0.65rem] font-medium tracking-wide">
            {tagline}
          </span>
        )}
      </span>
    </span>
  );
}
