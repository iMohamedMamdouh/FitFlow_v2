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
 */
export function LocaleSwitcher({ current }: { current: Locale }) {
  const [pending, startTransition] = useTransition();

  return (
    <div
      className="border-line inline-flex overflow-hidden rounded-full border text-xs"
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
            locale === current ? "bg-ink text-paper" : "text-subtle hover:text-ink hover:bg-raised",
          )}
        >
          {locale.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
