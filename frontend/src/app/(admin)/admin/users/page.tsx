import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { buttonStyles } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Link } from "@/components/ui/nav-link";
import { getAdminUsers } from "@/lib/api/admin-queries";
import { getCurrentUser } from "@/lib/api/queries";
import type { UserRole } from "@/lib/api/schema";
import { USER_ROLES } from "@/lib/api/schema";
import { CreateStaffForm } from "./create-staff-form";
import { UserRow } from "./user-row";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("admin.users");
  return { title: t("title") };
}

type Search = { role?: string; search?: string; status?: string };

function roleOf(value: string | undefined): UserRole | undefined {
  return (USER_ROLES as readonly string[]).includes(value ?? "") ? (value as UserRole) : undefined;
}

/**
 * قائمة المستخدمين.
 *
 * التصفية في الرابط لا في حالة عميل: البحث عن مستخدم بعينه ينتهي غالبًا
 * بإرسال الرابط أو العودة إليه بعد فعل، وحالة تعيش في الذاكرة تضيع في
 * الحالتين. نموذج `GET` عادي يكفي — بلا JavaScript أصلًا.
 */
export default async function AdminUsersPage({ searchParams }: { searchParams: Promise<Search> }) {
  const t = await getTranslations("admin.users");
  const roles = await getTranslations("roles");
  const params = await searchParams;

  const role = roleOf(params.role);
  const search = params.search?.trim() ?? "";
  const isActive =
    params.status === "active" ? true : params.status === "disabled" ? false : undefined;

  const [me, users] = await Promise.all([
    getCurrentUser(),
    getAdminUsers({ role, search: search || undefined, isActive }),
  ]);

  const filtered = role !== undefined || search !== "" || isActive !== undefined;

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1.5">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-subtle text-sm leading-7">{t("subtitle")}</p>
      </header>

      <form className="border-line bg-surface grid gap-4 rounded-xs border p-5 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end">
        <label className="flex flex-col gap-1.5">
          <span className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
            {t("search")}
          </span>
          <input
            type="search"
            name="search"
            defaultValue={search}
            placeholder={t("searchPlaceholder")}
            className="border-line border-b-line-strong bg-raised text-ink placeholder:text-faint rounded-xs border border-b-2 px-3.5 py-2.5 text-sm"
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
            {t("roleFilter")}
          </span>
          <select
            name="role"
            defaultValue={role ?? ""}
            className="border-line border-b-line-strong bg-raised text-ink rounded-xs border border-b-2 px-3.5 py-2.5 text-sm"
          >
            <option value="">{t("all")}</option>
            {USER_ROLES.map((value) => (
              <option key={value} value={value}>
                {roles(value)}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
            {t("statusFilter")}
          </span>
          <select
            name="status"
            defaultValue={params.status ?? ""}
            className="border-line border-b-line-strong bg-raised text-ink rounded-xs border border-b-2 px-3.5 py-2.5 text-sm"
          >
            <option value="">{t("all")}</option>
            <option value="active">{t("onlyActive")}</option>
            <option value="disabled">{t("onlyDisabled")}</option>
          </select>
        </label>

        <div className="flex gap-2">
          <button type="submit" className={buttonStyles({ size: "md" })}>
            {t("apply")}
          </button>
          {filtered && (
            <Link href="/admin/users" className={buttonStyles({ variant: "quiet", size: "md" })}>
              {t("reset")}
            </Link>
          )}
        </div>
      </form>

      {users.length === 0 ? (
        <Card>
          <CardHeader title={t("empty")} />
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {users.map((user) => (
            <UserRow key={user.id} user={user} isSelf={user.id === me.id} />
          ))}
        </div>
      )}

      <Card className="flex flex-col gap-5">
        <CardHeader title={t("createTitle")} description={t("createHint")} />
        <CreateStaffForm />
      </Card>
    </div>
  );
}
