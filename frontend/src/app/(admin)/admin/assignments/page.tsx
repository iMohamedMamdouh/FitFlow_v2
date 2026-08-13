import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { Alert, Badge } from "@/components/ui/alert";
import { Card, CardHeader } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { getAdminUsers } from "@/lib/api/admin-queries";
import { cn } from "@/lib/utils";
import { AssignForm, UnassignButton } from "./forms";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("admin.assignments");
  return { title: t("title") };
}

/**
 * إسناد المرضى للأخصائيين.
 *
 * الشاشة مبنية حول **الأخصائي المختار** لا حول جدول علاقات: السؤال الذي
 * يُطرح فعلًا هو "من يتابع هذا الأخصائي؟" و"من يحتاج متابعًا؟"، وجدول
 * بصفَّي معرّفات لا يجيب أيًّا منهما.
 *
 * الأخصائي المختار في الرابط: بعد كل إسناد تُعاد الصفحة، ولو كان الاختيار
 * في حالة عميل لعاد الاختيار إلى الصفر بعد كل فعل.
 */
export default async function AssignmentsPage({
  searchParams,
}: {
  searchParams: Promise<{ specialist?: string }>;
}) {
  const t = await getTranslations("admin.assignments");
  const params = await searchParams;

  const [specialists, patients] = await Promise.all([
    getAdminUsers({ role: "specialist", isActive: true }),
    getAdminUsers({ role: "patient" }),
  ]);

  const selected =
    specialists.find((specialist) => specialist.id === params.specialist) ?? specialists[0];

  // المطابقة بالمعرّف لا بالاسم: اسمان متطابقان لأخصائيين مختلفين حالة
  // واردة، ومطابقة الأسماء كانت ستُظهر مرضى أحدهما تحت الآخر.
  const follows = (patient: (typeof patients)[number]) =>
    patient.specialists.some((entry) => entry.id === selected?.id);

  const mine = selected ? patients.filter(follows) : [];
  const candidates = selected ? patients.filter((patient) => !follows(patient)) : [];
  const orphans = patients.filter((patient) => patient.specialists.length === 0);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      {specialists.length === 0 ? (
        <Alert tone="warning">{t("noSpecialists")}</Alert>
      ) : (
        <>
          <nav className="flex flex-wrap gap-2" aria-label={t("specialist")}>
            {specialists.map((specialist) => (
              <Link
                key={specialist.id}
                href={`/admin/assignments?specialist=${specialist.id}`}
                aria-current={specialist.id === selected?.id ? "true" : undefined}
                className={cn(
                  "cut cut-sm px-3.5 py-2 text-sm whitespace-nowrap transition-colors",
                  specialist.id === selected?.id
                    ? "bg-ink text-paper"
                    : "bg-raised text-subtle hover:text-ink",
                )}
              >
                {specialist.full_name}
                <span className="ms-2 tabular-nums opacity-70">{specialist.assigned_patients}</span>
              </Link>
            ))}
          </nav>

          {selected !== undefined && (
            <Card className="flex flex-col gap-6">
              <CardHeader title={selected.full_name} description={selected.email} />

              <AssignForm specialistId={selected.id} candidates={candidates} />

              <div className="flex flex-col gap-3">
                <h3 className="text-faint text-[0.7rem] font-semibold tracking-[0.12em] uppercase">
                  {t("currentPatients")}
                </h3>
                {mine.length === 0 ? (
                  <p className="text-subtle text-sm">{t("emptyForSpecialist")}</p>
                ) : (
                  <ul className="flex flex-col">
                    {mine.map((patient) => (
                      <li
                        key={patient.id}
                        className="border-line flex flex-wrap items-center justify-between gap-3 border-b py-3 last:border-b-0"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-medium">{patient.full_name}</p>
                          <p className="text-subtle text-xs break-all">{patient.email}</p>
                        </div>
                        <UnassignButton specialistId={selected.id} patientId={patient.id} />
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </Card>
          )}
        </>
      )}

      <Card className="flex flex-col gap-4">
        <CardHeader title={t("unassignedPatients")} />
        {patients.length === 0 ? (
          <p className="text-subtle text-sm">{t("noPatients")}</p>
        ) : orphans.length === 0 ? (
          <p className="text-subtle text-sm">{t("allAssigned")}</p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {orphans.map((patient) => (
              <li key={patient.id}>
                <Badge tone="warning">{patient.full_name}</Badge>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
