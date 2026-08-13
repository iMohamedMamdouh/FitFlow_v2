"use client";

import { useTransition } from "react";

import { LOCALES, LOCALE_LABELS, type Locale } from "@/i18n/config";
import { setLocaleAction } from "@/app/preferences-actions";
import { cn } from "@/lib/utils";

/**
 * تبديل اللغة.
 *
 * زران ظاهران لا قائمة منسدلة: اللغتان اثنتان فقط، وإظهارهما معًا يجعل
 * البديل مرئيًا لمن لا يقرأ اللغة الحالية — وهو بالضبط من يحتاج الزر.
 *
 * اللغة النشطة شريحة ليمونية بحبر داكن: لون ثابت يخالف الخلفية الفاتحة
 * والداكنة معًا، فيصلح الزر داخل اللوح الحبري في الشريط العلوي كما يصلح
 * فوق الورق.
 */
export function LocaleSwitcher({ current }: { current: Locale }) {
  const [pending, startTransition] = useTransition();

  return (
    <div
      className="inline-flex overflow-hidden rounded-xs border border-current/25 text-xs"
      role="group"
      aria-label={LOCALE_LABELS[current]}
    >
      {LOCALES.map((locale) => (
        <button
          key={locale}
          type="button"
          disabled={pending}
          aria-current={locale === current ? "true" : undefined}
          onClick={() => startTransition(() => setLocaleAction(locale))}
          className={cn(
            "px-2 py-1.5 font-medium transition-colors disabled:opacity-60 sm:px-2.5",
            locale === current
              ? "bg-signal text-signal-ink"
              : "text-current opacity-65 hover:opacity-100",
          )}
        >
          {locale.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
