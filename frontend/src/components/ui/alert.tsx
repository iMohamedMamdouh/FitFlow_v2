import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const alertStyles = cva("rounded-lg border px-4 py-3 text-sm leading-6", {
  variants: {
    tone: {
      info: "border-info/30 bg-info-soft text-info",
      success: "border-success/30 bg-success-soft text-success",
      warning: "border-warning/30 bg-warning-soft text-warning",
      danger: "border-danger/30 bg-danger-soft text-danger",
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

const badgeStyles = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "bg-muted-surface text-muted",
        primary: "bg-primary-soft text-primary-strong",
        success: "bg-success-soft text-success",
        warning: "bg-warning-soft text-warning",
        danger: "bg-danger-soft text-danger",
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
