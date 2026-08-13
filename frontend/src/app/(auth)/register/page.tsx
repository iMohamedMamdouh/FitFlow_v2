import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Link } from "@/components/ui/nav-link";
import { Card, CardHeader } from "@/components/ui/card";
import { RegisterForm } from "./register-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("auth");
  return { title: t("registerTitle") };
}

export default async function RegisterPage() {
  const t = await getTranslations("auth");

  return (
    <Card>
      <CardHeader title={t("registerTitle")} description={t("registerSubtitle")} />
      <RegisterForm />
      <p className="text-subtle mt-5 text-center text-sm">
        {t("haveAccount")}{" "}
        <Link href="/login" className="text-accent font-medium">
          {t("signIn")}
        </Link>
      </p>
      {/* التسجيل العام يُنشئ حساب مريض فقط — لا حقل دور في النموذج ولا في الـ API. */}
      <p className="text-subtle mt-2 text-center text-xs">{t("staffNotice")}</p>
    </Card>
  );
}
