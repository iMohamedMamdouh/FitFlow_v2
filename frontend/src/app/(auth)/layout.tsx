import { getTranslations } from "next-intl/server";
import { Link } from "@/components/ui/nav-link";

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  const app = await getTranslations("app");
  const consent = await getTranslations("consent");

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-6 px-5 py-12">
      <Link href="/" className="text-primary text-center text-lg font-bold">
        {app("name")}
        <span className="text-muted block text-xs font-normal">{app("tagline")}</span>
      </Link>
      {children}
      <p className="text-muted text-center text-xs leading-6">{consent("shortNotice")}</p>
    </main>
  );
}
