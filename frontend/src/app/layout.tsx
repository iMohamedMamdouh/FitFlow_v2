import type { Metadata, Viewport } from "next";
import { Cairo } from "next/font/google";
import "./globals.css";

// الخط العربي الأساسي للمنصة. متغير CSS عشان Tailwind يستخدمه.
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
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0b1120" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // ar + rtl مثبّتان من المستوى الجذري (قرار ADR-004).
  return (
    <html lang="ar" dir="rtl" className={cairo.variable}>
      <body className="bg-background text-foreground min-h-dvh font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
