"use client";

import { usePathname } from "next/navigation";

import { Link } from "@/components/ui/nav-link";
import { cn } from "@/lib/utils";

export type NavLink = { href: string; label: string };

/**
 * تنقّل التطبيق.
 *
 * شكلان لقائمة واحدة: **مسار جانبي** على الشاشات العريضة، وشريط شرائح
 * أفقي تحت الرأسية على ما دونها. المصدر واحد، فتعديل الروابط يحدث مرة
 * واحدة.
 *
 * المسار الجانبي مرسوم كخطوط مضمار: كل رابط خطّ رفيع على حافته البادئة،
 * والخطّ يضيء بلون الإشارة عند الوجهة الحالية. الرقم المتسلسل ليس زينة —
 * يعطي القائمة ترتيبًا يُحفظ بصريًا فيُقصد الرابط بموضعه لا بقراءته.
 *
 * الوجهة الحالية = أطول رابط يطابق المسار. المطابقة بالبادئة وحدها تجعل
 * `/specialist` مضيئًا داخل `/specialist/review` أيضًا، فيصبح لدينا
 * عنصران نشطان في قائمة واحدة.
 */
function useActiveHref(links: readonly NavLink[]): string | null {
  const pathname = usePathname();

  let best: string | null = null;
  for (const link of links) {
    const matches = pathname === link.href || pathname.startsWith(`${link.href}/`);
    if (matches && (best === null || link.href.length > best.length)) best = link.href;
  }
  return best;
}

export function NavRail({ links, label }: { links: readonly NavLink[]; label: string }) {
  const active = useActiveHref(links);

  return (
    <nav
      aria-label={label}
      className="sticky top-24 hidden w-52 shrink-0 flex-col self-start lg:flex"
    >
      {links.map((link, index) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={link.href === active ? "page" : undefined}
          className={cn(
            "flex items-center gap-3 border-s-2 py-2.5 ps-4 pe-3 text-sm transition-colors",
            link.href === active
              ? "border-s-signal bg-raised text-ink font-medium"
              : "border-s-line text-subtle hover:border-s-line-strong hover:text-ink",
          )}
        >
          <span aria-hidden="true" className="font-display text-[0.65rem] tabular-nums opacity-50">
            {String(index + 1).padStart(2, "0")}
          </span>
          {link.label}
        </Link>
      ))}
    </nav>
  );
}

export function NavStrip({ links, label }: { links: readonly NavLink[]; label: string }) {
  const active = useActiveHref(links);

  return (
    <nav
      aria-label={label}
      // التمرير الأفقي لا الطيّ خلف زر: مسارات تُستخدم يوميًا لا تُخفى.
      className="-mx-3 flex gap-2 overflow-x-auto px-3 py-4 lg:hidden"
    >
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={link.href === active ? "page" : undefined}
          className={cn(
            "cut cut-sm shrink-0 px-3.5 py-2 text-sm whitespace-nowrap transition-colors",
            link.href === active ? "bg-ink text-paper" : "bg-raised text-subtle hover:text-ink",
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
