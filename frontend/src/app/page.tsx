import Image from "next/image";
import { getTranslations } from "next-intl/server";

import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { SectionHeading } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { readLocale, readTheme } from "@/lib/preferences";

/**
 * الصفحة الخارجية.
 *
 * الصور كلها بدائل في `public/images/` — استبدل الملف بالاسم نفسه ولا
 * تحتاج تعديل أي كود. أبعادها مثبّتة في `<Image>` فلا تقفز الصفحة عند
 * التحميل مهما كانت الصورة البديلة.
 */

const FEATURE_KEYS = ["item1", "item2", "item3", "item4", "item5", "item6"] as const;
const STEP_KEYS = ["step1", "step2", "step3", "step4"] as const;
const FAQ_KEYS = ["1", "2", "3", "4"] as const;

export default async function LandingPage() {
  const [locale, theme] = await Promise.all([readLocale(), readTheme()]);
  const t = await getTranslations("landing");
  const consent = await getTranslations("consent");

  return (
    <>
      <SiteHeader locale={locale} theme={theme} />

      <main>
        {/* ─────────────────────────────────────────────── البطل */}
        <section className="relative overflow-hidden">
          <div
            aria-hidden="true"
            className="bg-grid pointer-events-none absolute inset-0 [mask-image:radial-gradient(70%_60%_at_50%_0%,black,transparent)] opacity-40"
          />
          <div className="relative mx-auto grid max-w-6xl gap-14 px-5 py-16 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:py-24">
            <div className="flex flex-col items-start gap-6">
              <Badge tone="clay">{t("hero.eyebrow")}</Badge>

              <h1 className="font-display text-4xl leading-[1.15] font-semibold tracking-tight text-balance sm:text-5xl">
                {t("hero.title")} <span className="text-accent">{t("hero.titleAccent")}</span>
              </h1>

              <p className="text-subtle max-w-xl text-lg leading-9">{t("hero.body")}</p>

              <div className="flex flex-wrap items-center gap-3">
                <Link href="/register" className={buttonStyles({ variant: "clay", size: "lg" })}>
                  {t("hero.primary")}
                </Link>
                <a href="#how" className={buttonStyles({ variant: "outline", size: "lg" })}>
                  {t("hero.secondary")}
                </a>
              </div>

              <p className="text-faint text-xs">{t("hero.note")}</p>
            </div>

            <div className="relative">
              {/* لوح خلفي مائل يعطي الصورة عمقًا بلا ظل ثقيل. */}
              <div
                aria-hidden="true"
                className="border-line bg-accent-wash absolute inset-0 -rotate-2 rounded-2xl border"
              />
              <Image
                src="/images/hero.svg"
                alt={t("hero.imageAlt")}
                width={960}
                height={640}
                priority
                className="border-line bg-surface shadow-card relative w-full rounded-2xl border"
              />
            </div>
          </div>
        </section>

        {/* ─────────────────────────────────────────────── أرقام */}
        <section className="border-line border-y">
          <div className="mx-auto grid max-w-6xl divide-y divide-[var(--color-line)] px-5 sm:grid-cols-3 sm:divide-x sm:divide-y-0 rtl:sm:divide-x-reverse">
            {(["engine", "review", "floor"] as const).map((key) => (
              <div key={key} className="flex flex-col gap-1.5 px-2 py-8 sm:px-8">
                <span className="text-faint text-[0.7rem] font-semibold tracking-[0.14em] uppercase">
                  {t(`stats.${key}Label`)}
                </span>
                <span className="font-display text-accent text-2xl font-semibold tracking-tight">
                  {t(`stats.${key}Value`)}
                </span>
                <span className="text-subtle text-sm">{t(`stats.${key}Hint`)}</span>
              </div>
            ))}
          </div>
        </section>

        {/* ─────────────────────────────────────────────── كيف يعمل */}
        <section id="how" className="scroll-mt-20">
          <div className="mx-auto max-w-6xl px-5 py-20">
            <SectionHeading
              eyebrow={t("how.eyebrow")}
              title={t("how.title")}
              description={t("how.body")}
            />

            <ol className="border-line mt-12 grid gap-px overflow-hidden rounded-2xl border bg-[var(--color-line)] sm:grid-cols-2 lg:grid-cols-4">
              {STEP_KEYS.map((key, index) => (
                <li key={key} className="bg-surface flex flex-col gap-3 p-7">
                  <span className="border-line text-accent font-display flex size-9 items-center justify-center rounded-full border text-sm font-semibold tabular-nums">
                    {index + 1}
                  </span>
                  <h3 className="font-display font-semibold tracking-tight">
                    {t(`how.${key}Title`)}
                  </h3>
                  <p className="text-subtle text-sm leading-7">{t(`how.${key}Body`)}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ─────────────────────────────────────────────── المميزات */}
        <section id="features" className="bg-raised/60 border-line scroll-mt-20 border-y">
          <div className="mx-auto max-w-6xl px-5 py-20">
            <SectionHeading
              eyebrow={t("features.eyebrow")}
              title={t("features.title")}
              description={t("features.body")}
            />

            <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {FEATURE_KEYS.map((key, index) => (
                <article
                  key={key}
                  className="border-line bg-surface flex flex-col gap-3 rounded-xl border p-6"
                >
                  <span className="bg-accent-wash text-accent font-display flex size-9 items-center justify-center rounded-lg text-sm font-semibold tabular-nums">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="font-display font-semibold tracking-tight">
                    {t(`features.${key}Title`)}
                  </h3>
                  <p className="text-subtle text-sm leading-7">{t(`features.${key}Body`)}</p>
                </article>
              ))}
            </div>

            <div className="mt-10 grid gap-5 sm:grid-cols-3">
              {["feature-nutrition", "feature-rehab", "feature-review"].map((name) => (
                <Image
                  key={name}
                  src={`/images/${name}.svg`}
                  alt={t("features.title")}
                  width={480}
                  height={320}
                  className="border-line bg-surface w-full rounded-xl border p-2"
                />
              ))}
            </div>
          </div>
        </section>

        {/* ─────────────────────────────────────────────── الأمان */}
        <section id="safety" className="scroll-mt-20">
          <div className="mx-auto grid max-w-6xl gap-14 px-5 py-20 lg:grid-cols-2 lg:items-center">
            <div>
              <SectionHeading
                eyebrow={t("safety.eyebrow")}
                title={t("safety.title")}
                description={t("safety.body")}
              />

              <ul className="mt-8 flex flex-col gap-4">
                {(["point1", "point2", "point3", "point4"] as const).map((key) => (
                  <li key={key} className="flex gap-3.5">
                    <CheckMark />
                    <span className="text-subtle text-sm leading-7">{t(`safety.${key}`)}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Image
              src="/images/safety.svg"
              alt={t("safety.imageAlt")}
              width={720}
              height={560}
              className="border-line bg-raised w-full rounded-2xl border p-2"
            />
          </div>
        </section>

        {/* ─────────────────────────────────────────────── أسئلة */}
        <section id="faq" className="border-line scroll-mt-20 border-t">
          <div className="mx-auto max-w-3xl px-5 py-20">
            <SectionHeading eyebrow={t("faq.eyebrow")} title={t("faq.title")} />

            <div className="divide-line mt-10 divide-y">
              {FAQ_KEYS.map((key) => (
                <details key={key} className="group py-5">
                  <summary className="font-display flex cursor-pointer list-none items-center justify-between gap-4 font-medium tracking-tight">
                    {t(`faq.q${key}`)}
                    <span
                      aria-hidden="true"
                      className="text-faint shrink-0 text-xl leading-none transition-transform group-open:rotate-45"
                    >
                      +
                    </span>
                  </summary>
                  <p className="text-subtle mt-3 text-sm leading-8">{t(`faq.a${key}`)}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* ─────────────────────────────────────────────── نداء أخير */}
        <section className="px-5 pb-20">
          <div className="bg-cta text-cta-ink border-accent/30 relative mx-auto max-w-6xl overflow-hidden rounded-2xl border px-8 py-14 sm:px-14">
            <div
              aria-hidden="true"
              className="bg-grid pointer-events-none absolute inset-0 opacity-15"
            />
            <div className="relative flex flex-col items-start gap-5">
              <h2 className="font-display max-w-2xl text-2xl leading-tight font-semibold tracking-tight text-balance sm:text-3xl">
                {t("cta.title")}
              </h2>
              <p className="max-w-xl text-base leading-8 opacity-85">{t("cta.body")}</p>
              <Link href="/register" className={buttonStyles({ variant: "clay", size: "lg" })}>
                {t("cta.button")}
              </Link>
              <p className="text-xs opacity-70">{consent("shortNotice")}</p>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </>
  );
}

function CheckMark() {
  return (
    <span
      aria-hidden="true"
      className="bg-accent-wash text-accent mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full"
    >
      <svg
        viewBox="0 0 24 24"
        className="size-3.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="m5 12.5 4.5 4.5L19 7.5" />
      </svg>
    </span>
  );
}
