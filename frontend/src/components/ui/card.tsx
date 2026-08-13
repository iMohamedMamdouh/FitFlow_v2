import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("border-border bg-surface rounded-xl border p-5 shadow-sm", className)}
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
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description !== undefined && (
          <p className="text-muted mt-1 text-sm leading-6">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}

/** رقم واحد بارز مع تسميته — لبطاقات لوحة المتابعة. */
export function Stat({
  label,
  value,
  hint,
}: {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
}) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-muted text-sm">{label}</span>
      <span className="text-2xl font-semibold tabular-nums">{value}</span>
      {hint !== undefined && <span className="text-muted text-xs">{hint}</span>}
    </Card>
  );
}
