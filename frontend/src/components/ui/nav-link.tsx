import NextLink, { type LinkProps } from "next/link";
import type { AnchorHTMLAttributes, ReactNode } from "react";

type Props = LinkProps & AnchorHTMLAttributes<HTMLAnchorElement> & { children: ReactNode };

/**
 * رابط داخلي **بلا prefetch**.
 *
 * ليس تفضيلًا في الأداء بل ضرورة أمنية. رمز التحديث في هذا النظام يدور،
 * والخادم يعتبر استخدام رمز سبق تدويره تسريبًا فيُبطل كل جلسات المستخدم.
 * طلبات الـ prefetch تُرسَل من المتصفح **متوازية** ومعها الكوكيز، فلو
 * صادفت نافذة التجديد لتسابق عدة طلبات على نفس الرمز وخرج المستخدم من
 * حسابه بلا سبب ظاهر له.
 *
 * التنقّل بدون prefetch أبطأ بأجزاء من الثانية، والبديل خروج عشوائي من
 * الحساب. لذلك كل رابط داخلي يمر من هنا لا من `next/link` مباشرة.
 */
export function Link({ children, ...props }: Props) {
  return (
    <NextLink prefetch={false} {...props}>
      {children}
    </NextLink>
  );
}
