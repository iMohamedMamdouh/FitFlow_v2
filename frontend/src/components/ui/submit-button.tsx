"use client";

import { useFormStatus } from "react-dom";

import { Button, type ButtonProps } from "./button";

/**
 * زر إرسال يعطّل نفسه أثناء تنفيذ الـ Server Action.
 *
 * `useFormStatus` يقرأ حالة أقرب `<form>` — لذلك لا يحتاج المكوّن أن
 * يُمرَّر إليه أي حالة، ولا يمكن أن يُنسى تعطيله في نموذج جديد.
 */
export function SubmitButton({
  children,
  pendingLabel,
  ...props
}: ButtonProps & { pendingLabel: string }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending} aria-busy={pending} {...props}>
      {pending ? pendingLabel : children}
    </Button>
  );
}
