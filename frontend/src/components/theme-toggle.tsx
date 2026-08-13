"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { PREFERENCE_MAX_AGE, THEME_COOKIE, type Theme } from "@/i18n/config";
import { cn } from "@/lib/utils";

/**
 * تبديل الوضع الفاتح/الداكن.
 *
 * التبديل يحدث في المتصفح مباشرة (سمة على `<html>` + كوكي) بلا نداء
 * للخادم: المظهر ألوان فقط، ونداء الخادم كان سيضيف تأخيرًا محسوسًا على
 * فعل يُتوقَّع أن يكون فوريًا. الكوكي يجعل الخادم يعرف الاختيار في الطلب
 * التالي فيصل `data-theme` صحيحًا من أول بايت بلا وميض.
 */
export function ThemeToggle({ initial }: { initial: Theme }) {
  const t = useTranslations("theme");
  const [theme, setTheme] = useState<Theme>(initial);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    document.cookie = `${THEME_COOKIE}=${next}; path=/; max-age=${PREFERENCE_MAX_AGE}; samesite=lax`;
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={t(theme === "dark" ? "toLight" : "toDark")}
      title={t(theme === "dark" ? "toLight" : "toDark")}
      className={cn(
        "border-line text-ink hover:border-accent hover:text-accent inline-flex size-8 sm:size-9",
        "items-center justify-center rounded-full border transition-colors",
      )}
    >
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="4" />
      <path
        strokeLinecap="round"
        d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"
      />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinejoin="round" d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
    </svg>
  );
}
