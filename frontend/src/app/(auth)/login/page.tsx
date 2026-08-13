import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Link } from "@/components/ui/nav-link";
import { Card, CardHeader } from "@/components/ui/card";
import { LoginForm } from "./login-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth");
  return { title: t("loginTitle") };
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const t = await getTranslations("auth");
  const { next } = await searchParams;

  return (
    <Card>
      <CardHeader title={t("loginTitle")} description={t("loginSubtitle")} />
      <LoginForm next={next ?? null} />
      <p className="text-subtle mt-5 text-center text-sm">
        {t("noAccount")}{" "}
        <Link href="/register" className="text-accent font-medium">
          {t("createOne")}
        </Link>
      </p>
    </Card>
  );
}
