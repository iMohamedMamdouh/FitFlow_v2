import { getTranslations } from "next-intl/server";

import { Link } from "@/components/ui/nav-link";
import { Card } from "@/components/ui/card";
import { buttonStyles } from "@/components/ui/button";

export default async function LandingPage() {
  const t = await getTranslations("landing");
  const app = await getTranslations("app");
  const consent = await getTranslations("consent");

  const features = [
    { title: t("feature1Title"), body: t("feature1Body") },
    { title: t("feature2Title"), body: t("feature2Body") },
    { title: t("feature3Title"), body: t("feature3Body") },
  ];

  return (
    <main className="mx-auto flex min-h-dvh max-w-4xl flex-col justify-center gap-10 px-5 py-16">
      <header className="flex flex-col gap-3">
        <p className="text-primary text-sm font-semibold">
          {app("name")} — {app("tagline")}
        </p>
        <h1 className="text-3xl leading-tight font-bold sm:text-4xl">{t("heroTitle")}</h1>
        <p className="text-muted max-w-2xl leading-8">{t("heroBody")}</p>
      </header>

      <div className="flex flex-wrap gap-3">
        <Link href="/register" className={buttonStyles({ size: "lg" })}>
          {t("start")}
        </Link>
        <Link href="/login" className={buttonStyles({ variant: "outline", size: "lg" })}>
          {t("login")}
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {features.map((feature) => (
          <Card key={feature.title} className="flex flex-col gap-2">
            <h2 className="font-semibold">{feature.title}</h2>
            <p className="text-muted text-sm leading-7">{feature.body}</p>
          </Card>
        ))}
      </div>

      <p className="text-muted border-border border-t pt-6 text-xs leading-6">
        {consent("shortNotice")} {consent("emergency")}
      </p>
    </main>
  );
}
