import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * التنبيهات.
 *
 * شريط ملوّن على الحافة البادئة بدل إطار ملوّن كامل: يميّز النبرة بوضوح
 * دون أن يتحوّل النص إلى كتلة لونية يصعب قراءتها — وهو ما يهم هنا لأن
 * أطول تنبيهات هذا التطبيق نصوص طبية تُقرأ فعلًا لا تُلمَح.
 */
const alertStyles = cva("rounded-xs border-s-[3px] px-4 py-3.5 text-sm leading-7", {
  variants: {
    tone: {
      info: "border-s-signal bg-accent-wash text-ink",
      success: "border-s-positive bg-positive-wash text-ink",
      warning: "border-s-caution bg-caution-wash text-ink",
      danger: "border-s-critical bg-critical-wash text-ink",
    },
  },
  defaultVariants: { tone: "info" },
});

export function Alert({
  tone,
  title,
  children,
  className,
}: VariantProps<typeof alertStyles> & {
  title?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div
      // الأخطاء تُعلَن لقارئات الشاشة — رسالة يراها المبصر فقط ليست رسالة.
      role={tone === "danger" ? "alert" : "status"}
      className={cn(alertStyles({ tone }), className)}
    >
      {title !== undefined && <p className="mb-1 font-semibold">{title}</p>}
      {children}
    </div>
  );
}

/**
 * الوسم.
 *
 * شريحة مستطيلة بزاوية مقصوصة لا كبسولة مستديرة. نبرة `signal` وحدها
 * مملوءة بالليموني الكامل — تُستخدم لما يحتاج انتباهًا فوريًا (خطة
 * تنتظر قرارًا مثلًا)، وبقيّة النبرات خلفية باهتة ونصّ ملوّن.
 */
const badgeStyles = cva(
  "cut cut-sm inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "bg-raised text-subtle",
        accent: "bg-accent-wash text-accent",
        signal: "bg-signal text-signal-ink",
        success: "bg-positive-wash text-positive",
        warning: "bg-caution-wash text-caution",
        danger: "bg-critical-wash text-critical",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export function Badge({
  tone,
  children,
  className,
}: VariantProps<typeof badgeStyles> & { children: ReactNode; className?: string }) {
  return <span className={cn(badgeStyles({ tone }), className)}>{children}</span>;
}
