import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * الأزرار.
 *
 * ثلاث درجات نداء لا خمس: `clay` للفعل الرئيسي في الشاشة (لون واحد لافت
 * لا يتكرر)، `solid` للأفعال العادية، و`outline`/`quiet` لما دونها.
 * تعدّد الأزرار البارزة في شاشة واحدة يلغي معنى البروز.
 *
 * الزوايا صغيرة (`rounded-lg` وأقل) عمدًا: الحواف شديدة الاستدارة هي أكثر
 * ما يعطي الواجهات طابعًا متشابهًا.
 */
const buttonStyles = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg font-medium tracking-tight " +
    "transition-all duration-150 disabled:pointer-events-none disabled:opacity-50 " +
    "active:translate-y-px",
  {
    variants: {
      variant: {
        clay: "bg-clay text-clay-ink hover:bg-clay-hover shadow-sm",
        solid: "bg-accent text-accent-ink hover:bg-accent-hover shadow-sm",
        outline:
          "border-line-strong text-ink hover:border-accent hover:text-accent border bg-transparent",
        quiet: "text-subtle hover:text-ink hover:bg-raised",
      },
      size: {
        sm: "h-9 px-3 text-sm sm:px-3.5",
        md: "h-11 px-5 text-sm",
        lg: "h-12 px-7 text-base",
      },
      block: { true: "w-full", false: "" },
    },
    defaultVariants: { variant: "solid", size: "md", block: false },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonStyles>;

export function Button({ className, variant, size, block, ...props }: ButtonProps) {
  return <button className={cn(buttonStyles({ variant, size, block }), className)} {...props} />;
}

export { buttonStyles };
