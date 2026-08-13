import type { Metadata, Viewport } from "next";
import { Cairo } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";

import { LOCALE, TIME_ZONE } from "@/i18n/request";
import "./globals.css";

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: "--font-cairo",
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
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
    { media: "(prefers-color-scheme: dark)", color: "#020617" },
  ],
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // ar + rtl مثبّتان من المستوى الجذري (قرار ADR-004).
  const messages = await getMessages();

  return (
    <html lang={LOCALE} dir="rtl" className={cairo.variable}>
      <body className="bg-background text-foreground min-h-dvh font-sans antialiased">
        <NextIntlClientProvider locale={LOCALE} timeZone={TIME_ZONE} messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
