import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("border-line bg-surface shadow-card rounded-xl border p-6", className)}
      {...props}
    />
  );
}

export function CardHeader({
  title,
  description,
  action,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <h2 className="font-display text-base font-semibold tracking-tight">{title}</h2>
        {description !== undefined && (
          <p className="text-subtle mt-1.5 text-sm leading-6">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}

/**
 * رقم واحد بارز مع تسميته.
 *
 * التسمية صغيرة بحروف متباعدة فوق الرقم، والرقم بخط العرض بوزن ثقيل:
 * ترتيب يجعل القيمة هي أول ما تقع عليه العين في شبكة من البطاقات.
 */
export function Stat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "default" | "accent";
}) {
  return (
    <div className="border-line bg-surface rounded-xl border p-5">
      <span className="text-faint text-[0.7rem] font-medium tracking-[0.12em] uppercase">
        {label}
      </span>
      <p
        className={cn(
          "font-display mt-2 text-3xl leading-none font-semibold tabular-nums",
          tone === "accent" && "text-accent",
        )}
      >
        {value}
      </p>
      {hint !== undefined && <p className="text-subtle mt-2 text-xs leading-5">{hint}</p>}
    </div>
  );
}

/** عنوان قسم في الصفحة الخارجية — تسمية صغيرة فوق عنوان كبير. */
export function SectionHeading({
  eyebrow,
  title,
  description,
  className,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex max-w-2xl flex-col gap-3", className)}>
      {eyebrow !== undefined && (
        <span className="text-clay text-xs font-semibold tracking-[0.18em] uppercase">
          {eyebrow}
        </span>
      )}
      <h2 className="font-display text-2xl leading-tight font-semibold tracking-tight sm:text-3xl">
        {title}
      </h2>
      {description !== undefined && (
        <p className="text-subtle text-base leading-8">{description}</p>
      )}
    </div>
  );
}
