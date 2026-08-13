import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * البطاقة.
 *
 * مستطيل شبه حادّ بحدّ رفيع. البروز — حين يُطلب — خطّ إشارة ليموني على
 * الحافة العليا لا إطار ملوّن كامل: الإطار الكامل يصبغ محتوى البطاقة
 * بنبرة لونية، وأغلب ما بداخلها هنا أرقام طبية تُقرأ لا تُلمَح.
 */
export function Card({
  featured = false,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & { featured?: boolean }) {
  return (
    <div
      className={cn(
        "border-line bg-surface shadow-card rounded-xs border p-6",
        featured && "rule-signal",
        className,
      )}
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
 * التسمية صغيرة بحروف متباعدة فوق الرقم، والرقم بخط العرض بوزن ثقيل،
 * وتحته علامة قياس قصيرة. الترتيب يجعل القيمة أول ما تقع عليه العين في
 * شبكة من البطاقات.
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
    <div className="border-line bg-surface relative rounded-xs border p-5">
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
      <span
        aria-hidden="true"
        className={cn("mt-3 block h-0.5 w-8", tone === "accent" ? "bg-signal" : "bg-line-strong")}
      />
      {hint !== undefined && <p className="text-subtle mt-2 text-xs leading-5">{hint}</p>}
    </div>
  );
}

/**
 * عنوان قسم — تسمية صغيرة مسبوقة بعلامة إشارة، فوق عنوان كبير.
 *
 * التسمية بلون النص لا بلون الإشارة: الليموني لا يُقرأ نصًّا على خلفية
 * فاتحة، فدوره هنا العلامة الصغيرة قبله.
 */
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
        <span className="text-ink inline-flex items-center gap-2.5 text-xs font-semibold tracking-[0.18em] uppercase">
          <span aria-hidden="true" className="bg-signal inline-block h-2.5 w-6" />
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
