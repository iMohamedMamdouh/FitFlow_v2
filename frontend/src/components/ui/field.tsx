"use client";

import { useId } from "react";
import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";

const controlStyles =
  "border-border bg-surface text-foreground placeholder:text-muted w-full rounded-lg border " +
  "px-3 py-2.5 text-sm transition-colors disabled:opacity-60";

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
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      {children}
      {hint !== undefined && error == null && (
        <p className="text-muted text-xs leading-5">{hint}</p>
      )}
      {/* الخطأ يُربط بالحقل عبر aria-describedby لا بالقرب البصري فقط. */}
      {error != null && (
        <p id={`${id}-error`} role="alert" className="text-danger text-xs leading-5">
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
        className={cn(controlStyles, error != null && "border-danger", className)}
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
        className={cn(controlStyles, error != null && "border-danger", className)}
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
        className={cn(controlStyles, "resize-y", error != null && "border-danger", className)}
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
      <div className="flex items-start gap-2.5">
        <input
          id={id}
          type="checkbox"
          className={cn("accent-primary mt-1 size-4 shrink-0", className)}
          aria-describedby={error != null ? `${id}-error` : undefined}
          {...props}
        />
        <label htmlFor={id} className="text-sm leading-6">
          {label}
        </label>
      </div>
      {hint !== undefined && <p className="text-muted ms-6.5 text-xs leading-5">{hint}</p>}
      {error != null && (
        <p id={`${id}-error`} role="alert" className="text-danger ms-6.5 text-xs leading-5">
          {error}
        </p>
      )}
    </div>
  );
}
