import type { Metadata, Viewport } from "next";
import { Alexandria, Readex_Pro } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";

import { TIME_ZONE, directionOf } from "@/i18n/config";
import { readLocale, readTheme } from "@/lib/preferences";
import "./globals.css";

// خطّان يدعمان العربية واللاتينية معًا — فلا يتغيّر إحساس الصفحة عند
// تبديل اللغة، ولا نحمّل خطًا ثالثًا لكل لغة. Readex Pro مرسوم أصلًا
// لقراءة طويلة بالعربية، وAlexandria هندسي عريض يعطي العناوين والأرقام
// نبرة أداة قياس لا نبرة مقال.
const readex = Readex_Pro({
  subsets: ["arabic", "latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-readex",
  display: "swap",
});

const alexandria = Alexandria({
  subsets: ["arabic", "latin"],
  weight: ["500", "600", "700"],
  variable: "--font-alexandria",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "FitFlow — منصة الصحة والتأهيل الرياضي",
    template: "%s | FitFlow",
  },
  description:
    "منصة ذكية للتأهيل من الإصابات وإدارة الوزن والتغذية الشخصية — أداة دعم قرار للأخصائيين.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f2f4ee" },
    { media: "(prefers-color-scheme: dark)", color: "#0f1210" },
  ],
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // اللغة والمظهر يُقرآن على الخادم: الصفحة تصل بالاتجاه والألوان
  // الصحيحة من أول بايت، بلا وميض ولا قفزة تخطيط.
  const [locale, theme, messages] = await Promise.all([readLocale(), readTheme(), getMessages()]);

  return (
    <html
      lang={locale}
      dir={directionOf(locale)}
      data-theme={theme}
      className={`${readex.variable} ${alexandria.variable}`}
    >
      <body className="bg-paper text-ink min-h-dvh font-sans antialiased">
        <NextIntlClientProvider locale={locale} timeZone={TIME_ZONE} messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
