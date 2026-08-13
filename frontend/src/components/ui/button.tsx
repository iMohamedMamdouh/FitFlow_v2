import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * الأزرار.
 *
 * ثلاث درجات نداء لا خمس: `signal` للفعل الرئيسي في الشاشة (ليموني مملوء
 * بحبر داكن، لا يتكرر مرتين في شاشة واحدة)، `solid` كتلة حبرية للأفعال
 * العادية، و`outline`/`quiet` لما دونها. تعدّد الأزرار البارزة يلغي معنى
 * البروز.
 *
 * الشكل: زاوية واحدة مقصوصة قُطريًا في الطرازين المملوءين. القصّة تحذف
 * الحدّ على القُطر، فالطرازان ذوا الإطار (`outline`/`quiet`) يبقيان
 * مستطيلين — إطار مقطوع بلا خطّ أسوأ من إطار كامل.
 */
const buttonStyles = cva(
  "inline-flex items-center justify-center gap-2 font-medium tracking-tight " +
    "transition-all duration-150 disabled:pointer-events-none disabled:opacity-50 " +
    "active:translate-y-px",
  {
    variants: {
      variant: {
        signal: "cut cut-sm bg-signal text-signal-ink hover:bg-signal-hover",
        solid: "cut cut-sm bg-ink text-paper hover:bg-ink/90",
        outline:
          "rounded-xs border border-line-strong text-ink hover:border-accent hover:text-accent bg-transparent",
        quiet: "rounded-xs text-subtle hover:text-ink hover:bg-raised",
        // `ghost` مرسوم بألوان نسبية ليعمل داخل اللوح الحبري في الشريط
        // العلوي: `quiet` هناك نصّ رمادي داكن على خلفية داكنة، أي لا شيء.
        ghost: "rounded-xs text-current opacity-70 hover:opacity-100 hover:bg-current/10",
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
