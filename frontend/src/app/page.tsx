import Image from "next/image";
import { getTranslations } from "next-intl/server";

import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/alert";
import { buttonStyles } from "@/components/ui/button";
import { SectionHeading } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { getVisitor } from "@/lib/api/queries";
import { homeForRole, workspaceKey } from "@/lib/auth/roles";
import { readLocale, readTheme } from "@/lib/preferences";

/**
 * الصفحة الخارجية.
 *
 * الصفحة مفتوحة للجميع وهي واجهة المنصة: يراها الزائر والمسجَّل معًا.
 * لذلك النداءان الرئيسيان يتبعان الجلسة — "ابدأ مجانًا" لمن لا حساب له،
 * وزرّ يفتح مساحته لمن سجّل دخوله. عرض "أنشئ حسابًا" لمن هو داخل حسابه
 * بالفعل دعوة إلى طريق مسدود.
 *
 * الصور في `public/images/` بأبعادها النهائية تمامًا (960×640 للبطل،
 * 720×560 للأمان، 480×320 للمميزات). الأبعاد مثبّتة في `<Image>` أيضًا،
 * فلا تقفز الصفحة أثناء التحميل. لاستبدال صورة: ضع ملفًا بالاسم نفسه
 * وبالمقاس نفسه — أي نسبة مختلفة ستُمطّ.
 */

const FEATURE_KEYS = ["item1", "item2", "item3", "item4", "item5", "item6"] as const;
const STEP_KEYS = ["step1", "step2", "step3", "step4"] as const;
const FAQ_KEYS = ["1", "2", "3", "4"] as const;

export default async function LandingPage() {
  const [locale, theme, visitor] = await Promise.all([readLocale(), readTheme(), getVisitor()]);
  const t = await getTranslations("landing");
  const consent = await getTranslations("consent");
  const translate = await getTranslations();

  const primary =
    visitor === null
      ? { href: "/register", label: t("hero.primary") }
      : { href: homeForRole(visitor.role), label: translate(workspaceKey(visitor.role)) };

  return (
    <>
      <SiteHeader locale={locale} theme={theme} />

      <main>
        {/* ─────────────────────────────────────────────── البطل */}
        <section className="relative overflow-hidden">
          <div
            aria-hidden="true"
            className="bg-lanes pointer-events-none absolute inset-0 [mask-image:linear-gradient(to_bottom,black,transparent)]"
          />
          <div className="relative mx-auto grid max-w-6xl gap-14 px-5 py-14 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:py-20">
            <div className="flex flex-col items-start gap-6">
              <Badge tone="signal">{t("hero.eyebrow")}</Badge>

              <h1 className="font-display text-4xl leading-[1.3] font-semibold tracking-tight text-balance sm:text-5xl sm:leading-[1.25]">
                {t("hero.title")}{" "}
                {/* الكلمة المميّزة مظلّلة بالليموني لا مكتوبة به: النص
                    الليموني على ورق فاتح لا يُقرأ، والتظليل يعطي التمييز
                    نفسه بتباين كامل. */}
                <span className="bg-signal text-signal-ink box-decoration-clone px-2 py-0.5">
                  {t("hero.titleAccent")}
                </span>
              </h1>

              <p className="text-subtle max-w-xl text-lg leading-9">{t("hero.body")}</p>

              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href={primary.href}
                  className={buttonStyles({ variant: "signal", size: "lg" })}
                >
                  {primary.label}
                </Link>
                <a href="#how" className={buttonStyles({ variant: "outline", size: "lg" })}>
                  {t("hero.secondary")}
                </a>
              </div>

              {/* "لا يحتاج بطاقة ائتمان · التسجيل في دقيقتين" كلام موجّه
                  لمن لم يسجّل بعد. */}
              {visitor === null && <p className="text-faint text-xs">{t("hero.note")}</p>}
            </div>

            <div className="relative">
              {/* لوح خلفي مزاح بمقدار ثابت — عمق بحافة حادّة لا بظلّ ناعم. */}
              <div
                aria-hidden="true"
                className="bg-accent-wash border-line absolute inset-0 translate-x-3 translate-y-3 border rtl:-translate-x-3"
              />
              <Image
                src="/images/img9.webp"
                alt={t("hero.imageAlt")}
                width={960}
                height={640}
                priority
                className="border-line bg-surface relative w-full border"
              />
            </div>
          </div>
        </section>

        {/* ─────────────────────────────────────────────── أرقام */}
        <section className="border-line border-y">
          <div className="mx-auto grid max-w-6xl divide-y divide-[var(--color-line)] px-5 sm:grid-cols-3 sm:divide-x sm:divide-y-0 rtl:sm:divide-x-reverse">
            {(["engine", "review", "floor"] as const).map((key) => (
              <div key={key} className="flex flex-col items-start gap-2 px-2 py-8 sm:px-8">
                <span className="text-faint text-[0.7rem] font-semibold tracking-[0.14em] uppercase">
                  {t(`stats.${key}Label`)}
                </span>
                <span className="font-display text-2xl font-semibold tracking-tight">
                  {t(`stats.${key}Value`)}
                </span>
                <span aria-hidden="true" className="bg-signal h-0.5 w-8" />
                <span className="text-subtle text-sm">{t(`stats.${key}Hint`)}</span>
              </div>
            ))}
          </div>
        </section>

        {/* ─────────────────────────────────────────────── كيف يعمل */}
        <section id="how" className="scroll-mt-24">
          <div className="mx-auto max-w-6xl px-5 py-20">
            <SectionHeading
              eyebrow={t("how.eyebrow")}
              title={t("how.title")}
              description={t("how.body")}
            />

            {/* مسارات: كل خطوة عمود يبدأ بخطّ علوي، وخطّ الخطوة الأولى
                وحده بلون الإشارة — نقطة البداية تُقرأ من الشكل لا من
                الرقم وحده. */}
            <ol className="mt-12 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
              {STEP_KEYS.map((key, index) => (
                <li key={key} className="flex flex-col gap-3">
                  <span
                    aria-hidden="true"
                    className={index === 0 ? "bg-signal h-1 w-full" : "bg-line-strong h-1 w-full"}
                  />
                  <span className="font-display text-faint text-xs font-semibold tabular-nums">
                    {String(index + 1).padStart(2, "0")}
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
        <section id="features" className="bg-raised/50 border-line scroll-mt-24 border-y">
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
                  className="border-line bg-surface flex flex-col gap-3 rounded-xs border p-6"
                >
                  <span className="bg-ink text-paper font-display cut cut-sm flex size-9 items-center justify-center text-sm font-semibold tabular-nums">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="font-display font-semibold tracking-tight">
                    {t(`features.${key}Title`)}
                  </h3>
                  <p className="text-subtle text-sm leading-7">{t(`features.${key}Body`)}</p>
                </article>
              ))}
            </div>

            {/* صور توضيحية: `alt` فارغ عمدًا. النص المجاور يصف المميزات
                بالفعل، وتكرار الوصف نفسه ثلاث مرات ضجيج على قارئ الشاشة. */}
            <div className="mt-10 grid gap-5 sm:grid-cols-3">
              {["img7", "img3", "img1"].map((name) => (
                <Image
                  key={name}
                  src={`/images/${name}.webp`}
                  alt=""
                  width={480}
                  height={320}
                  className="border-line bg-surface w-full rounded-xs border"
                />
              ))}
            </div>
          </div>
        </section>

        {/* ─────────────────────────────────────────────── الأمان */}
        <section id="safety" className="scroll-mt-24">
          <div className="mx-auto grid max-w-6xl gap-14 px-5 py-20 lg:grid-cols-2 lg:items-center">
            <div>
              <SectionHeading
                eyebrow={t("safety.eyebrow")}
                title={t("safety.title")}
                description={t("safety.body")}
              />

              {/* علامات قياس على خطّ رأسي بدل صفّ من علامات ✓ — النقاط هنا
                  حدود سلامة متتابعة لا قائمة مزايا. */}
              <ul className="border-line mt-8 flex flex-col border-s">
                {(["point1", "point2", "point3", "point4"] as const).map((key) => (
                  <li key={key} className="relative py-3 ps-5">
                    <span
                      aria-hidden="true"
                      className="bg-signal absolute start-0 top-5 h-0.5 w-3"
                    />
                    <span className="text-subtle text-sm leading-7">{t(`safety.${key}`)}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Image
              src="/images/img5.webp"
              alt={t("safety.imageAlt")}
              width={720}
              height={560}
              className="border-line bg-surface w-full rounded-xs border"
            />
          </div>
        </section>

        {/* ─────────────────────────────────────────────── أسئلة */}
        <section id="faq" className="border-line scroll-mt-24 border-t">
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
        <section className="px-3 pb-20 sm:px-5">
          <div className="bg-slab text-slab-ink cut cut-lg relative mx-auto max-w-6xl overflow-hidden px-8 py-14 sm:px-14">
            <div
              aria-hidden="true"
              className="bg-lanes pointer-events-none absolute inset-0 opacity-20"
            />
            <div className="relative flex flex-col items-start gap-5">
              <span aria-hidden="true" className="bg-signal h-1 w-12" />
              <h2 className="font-display max-w-2xl text-2xl leading-tight font-semibold tracking-tight text-balance sm:text-3xl">
                {t("cta.title")}
              </h2>
              <p className="max-w-xl text-base leading-8 opacity-85">{t("cta.body")}</p>
              <Link href={primary.href} className={buttonStyles({ variant: "signal", size: "lg" })}>
                {visitor === null ? t("cta.button") : primary.label}
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
