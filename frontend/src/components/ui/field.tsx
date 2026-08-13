"use client";

import { useId } from "react";
import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";

/**
 * حقول الإدخال.
 *
 * التسمية صغيرة بحروف متباعدة فوق الحقل، والحقل نفسه بخلفية `raised`
 * وحد رفيع يتلوّن بلون الهوية عند التركيز. المظهر مقصود ليقرأ كنموذج
 * طبي منظّم لا كصندوق بحث.
 */

const controlStyles =
  "w-full rounded-lg border border-line bg-raised px-3.5 py-2.5 text-sm text-ink " +
  "placeholder:text-faint transition-colors hover:border-line-strong " +
  "focus:border-accent disabled:opacity-60";

function Label({ htmlFor, children }: { htmlFor: string; children: ReactNode }) {
  return (
    <label
      htmlFor={htmlFor}
      className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase"
    >
      {children}
    </label>
  );
}

function Wrapper({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: string | null;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint !== undefined && error == null && (
        <p className="text-subtle text-xs leading-5">{hint}</p>
      )}
      {/* الخطأ يُربط بالحقل عبر aria-describedby لا بالقرب البصري فقط. */}
      {error != null && (
        <p id={`${id}-error`} role="alert" className="text-critical text-xs leading-5">
          {error}
        </p>
      )}
    </div>
  );
}

type FieldProps = {
  label: ReactNode;
  hint?: ReactNode;
  error?: string | null;
};

export function TextField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <input
        id={id}
        aria-invalid={error != null}
        aria-describedby={error != null ? `${id}-error` : undefined}
        className={cn(controlStyles, error != null && "border-critical", className)}
        {...props}
      />
    </Wrapper>
  );
}

export function SelectField({
  label,
  hint,
  error,
  className,
  children,
  ...props
}: FieldProps & SelectHTMLAttributes<HTMLSelectElement>) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <select
        id={id}
        aria-invalid={error != null}
        aria-describedby={error != null ? `${id}-error` : undefined}
        className={cn(
          controlStyles,
          "appearance-none",
          error != null && "border-critical",
          className,
        )}
        {...props}
      >
        {children}
      </select>
    </Wrapper>
  );
}

export function TextAreaField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <textarea
        id={id}
        rows={3}
        aria-invalid={error != null}
        aria-describedby={error != null ? `${id}-error` : undefined}
        className={cn(controlStyles, "resize-y", error != null && "border-critical", className)}
        {...props}
      />
    </Wrapper>
  );
}

export function CheckboxField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-start gap-3">
        <input
          id={id}
          type="checkbox"
          className={cn("accent-accent mt-0.5 size-4 shrink-0", className)}
          aria-describedby={error != null ? `${id}-error` : undefined}
          {...props}
        />
        <label htmlFor={id} className="text-sm leading-6">
          {label}
        </label>
      </div>
      {hint !== undefined && <p className="text-subtle ms-7 text-xs leading-5">{hint}</p>}
      {error != null && (
        <p id={`${id}-error`} role="alert" className="text-critical ms-7 text-xs leading-5">
          {error}
        </p>
      )}
    </div>
  );
}

/**
 * مربّع اختيار بمظهر بطاقة — لقوائم مثل مسبّبات الحساسية.
 *
 * مساحة النقر كاملة البطاقة لا المربّع وحده: القوائم الطويلة على الموبايل
 * تُخطئ كثيرًا حين تكون المساحة القابلة للنقر بحجم مربّع.
 */
export function CheckboxCard({
  label,
  className,
  ...props
}: { label: ReactNode } & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <label
      htmlFor={id}
      className={cn(
        "border-line bg-surface hover:border-accent flex cursor-pointer items-center gap-3",
        "rounded-lg border px-3.5 py-3 text-sm transition-colors",
        "has-[:checked]:border-accent has-[:checked]:bg-accent-wash",
        className,
      )}
    >
      <input id={id} type="checkbox" className="accent-accent size-4 shrink-0" {...props} />
      <span>{label}</span>
    </label>
  );
}
